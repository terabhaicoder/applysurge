"""
Export service for generating CSV/XLSX exports.
"""

import csv
import io
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.analytics import Export
from app.models.application import Application
from app.services.s3_service import S3Service


class ExportService:
    """Service for generating and managing data exports."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.s3 = S3Service()

    async def list_exports(self, user_id: UUID) -> List[dict]:
        """List all exports for a user."""
        result = await self.db.execute(
            select(Export)
            .where(Export.user_id == user_id)
            .order_by(desc(Export.created_at))
        )
        exports = result.scalars().all()
        return [
            {
                "id": str(e.id),
                "user_id": str(e.user_id),
                "export_type": e.export_type,
                "file_name": e.file_name,
                "file_url": e.file_url,
                "status": e.status,
                "record_count": e.total_records,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in exports
        ]

    async def create_export(
        self,
        user_id: UUID,
        export_type: str = "applications",
        format: str = "csv",
    ) -> dict:
        """Create a new export job."""
        export = Export(
            user_id=user_id,
            export_type=export_type,
            format=format,
            status="processing",
            file_name=f"{export_type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.{format}",
        )
        self.db.add(export)
        await self.db.flush()
        await self.db.refresh(export)

        # Generate export synchronously for CSV (for large exports, use Celery)
        try:
            if export_type == "applications":
                content, count = await self._export_applications(user_id, format)
            else:
                content, count = b"", 0

            # Upload to S3
            file_key = f"exports/{user_id}/{export.file_name}"
            content_type = "text/csv" if format == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            file_url = await self.s3.upload_file(content, file_key, content_type)

            export.status = "completed"
            export.file_url = file_url
            export.total_records = count
            await self.db.flush()

        except Exception as e:
            export.status = "failed"
            export.error_message = str(e)
            await self.db.flush()

        return {
            "id": str(export.id),
            "status": export.status,
            "file_name": export.file_name,
            "record_count": export.total_records,
        }

    async def get_export(self, user_id: UUID, export_id: UUID) -> dict:
        """Get export status."""
        result = await self.db.execute(
            select(Export).where(
                Export.id == export_id,
                Export.user_id == user_id,
            )
        )
        export = result.scalar_one_or_none()
        if not export:
            raise NotFoundError("Export")

        return {
            "id": str(export.id),
            "user_id": str(export.user_id),
            "export_type": export.export_type,
            "file_name": export.file_name,
            "file_url": export.file_url,
            "status": export.status,
            "record_count": export.total_records,
            "created_at": export.created_at.isoformat() if export.created_at else None,
        }

    async def get_download_url(self, user_id: UUID, export_id: UUID) -> str:
        """Get a presigned download URL for an export."""
        result = await self.db.execute(
            select(Export).where(
                Export.id == export_id,
                Export.user_id == user_id,
            )
        )
        export = result.scalar_one_or_none()
        if not export:
            raise NotFoundError("Export")

        if export.status != "completed":
            raise NotFoundError("Export not ready for download")

        file_key = f"exports/{user_id}/{export.file_name}"
        return await self.s3.get_presigned_url(file_key)

    async def _export_applications(
        self, user_id: UUID, format: str
    ) -> Tuple[bytes, int]:
        """Export applications to CSV format."""
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(Application)
            .options(selectinload(Application.job))
            .where(Application.user_id == user_id)
            .order_by(Application.created_at.desc())
        )
        applications = result.scalars().all()

        if format == "csv":
            return self._to_csv(applications), len(applications)
        else:
            return self._to_csv(applications), len(applications)

    def _to_csv(self, applications) -> bytes:
        """Convert applications to CSV bytes."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Job Title",
            "Company",
            "Status",
            "Applied At",
            "Source",
            "Response Received",
            "Response Date",
            "Notes",
            "Application URL",
        ])

        # Data rows
        for app in applications:
            writer.writerow([
                app.job.title if app.job else "",
                app.job.company if app.job else "",
                app.status or "",
                app.applied_at.isoformat() if app.applied_at else "",
                app.applied_via or "",
                "Yes" if app.response_received else "No",
                app.response_received_at.isoformat() if app.response_received_at else "",
                app.notes or "",
                app.application_url or "",
            ])

        return output.getvalue().encode("utf-8")
