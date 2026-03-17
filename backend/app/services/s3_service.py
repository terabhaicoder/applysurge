"""
S3-compatible file storage service.
Works with AWS S3, MinIO, Cloudflare R2, and other compatible services.
"""

import os
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings


class S3Service:
    """Service for S3-compatible file storage operations."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy-initialize the S3 client."""
        if self._client is None:
            config = Config(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "adaptive"},
            )

            client_kwargs = {
                "service_name": "s3",
                "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
                "region_name": settings.AWS_S3_REGION,
                "config": config,
            }

            # Support custom endpoints for MinIO/R2
            endpoint_url = os.environ.get("S3_ENDPOINT_URL")
            if endpoint_url:
                client_kwargs["endpoint_url"] = endpoint_url

            self._client = boto3.client(**client_kwargs)

        return self._client

    @property
    def bucket(self) -> str:
        """Get the configured bucket name."""
        return settings.AWS_S3_BUCKET

    async def upload_file(
        self,
        file_content: bytes,
        key: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload a file to S3.

        Args:
            file_content: Raw bytes of the file.
            key: The S3 object key (path).
            content_type: MIME type of the file.
            metadata: Optional metadata dict.

        Returns:
            The URL of the uploaded file.
        """
        if settings.STORAGE_BACKEND == "local":
            return await self._upload_local(file_content, key)

        extra_args = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = metadata

        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_content,
                **extra_args,
            )

            # Return the object URL
            endpoint = os.environ.get("S3_ENDPOINT_URL", f"https://{self.bucket}.s3.{settings.AWS_S3_REGION}.amazonaws.com")
            if "amazonaws.com" in endpoint:
                return f"https://{self.bucket}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{key}"
            else:
                return f"{endpoint}/{self.bucket}/{key}"

        except ClientError as e:
            raise RuntimeError(f"S3 upload failed: {str(e)}")

    async def download_file(self, key: str) -> Optional[bytes]:
        """
        Download a file from S3.

        Args:
            key: The S3 object key.

        Returns:
            File content as bytes, or None if not found.
        """
        if settings.STORAGE_BACKEND == "local":
            return await self._download_local(key)

        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise RuntimeError(f"S3 download failed: {str(e)}")

    async def delete_file(self, key: str) -> bool:
        """
        Delete a file from S3.

        Args:
            key: The S3 object key.

        Returns:
            True if deleted successfully.
        """
        if settings.STORAGE_BACKEND == "local":
            return await self._delete_local(key)

        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            raise RuntimeError(f"S3 delete failed: {str(e)}")

    async def get_presigned_url(
        self, key: str, expiration: int = 3600
    ) -> str:
        """
        Generate a presigned URL for file download.

        Args:
            key: The S3 object key.
            expiration: URL expiration in seconds (default 1 hour).

        Returns:
            Presigned URL string.
        """
        if settings.STORAGE_BACKEND == "local":
            return f"/api/v1/files/{key}"

        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            raise RuntimeError(f"Failed to generate presigned URL: {str(e)}")

    async def file_exists(self, key: str) -> bool:
        """Check if a file exists in S3."""
        if settings.STORAGE_BACKEND == "local":
            path = os.path.join(settings.STORAGE_LOCAL_PATH, key)
            return os.path.exists(path)

        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    # Local storage fallback methods
    async def _upload_local(self, file_content: bytes, key: str) -> str:
        """Upload file to local filesystem."""
        path = os.path.join(settings.STORAGE_LOCAL_PATH, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "wb") as f:
            f.write(file_content)

        return f"/storage/{key}"

    async def _download_local(self, key: str) -> Optional[bytes]:
        """Download file from local filesystem."""
        path = os.path.join(settings.STORAGE_LOCAL_PATH, key)
        if not os.path.exists(path):
            return None

        with open(path, "rb") as f:
            return f.read()

    async def _delete_local(self, key: str) -> bool:
        """Delete file from local filesystem."""
        path = os.path.join(settings.STORAGE_LOCAL_PATH, key)
        if os.path.exists(path):
            os.remove(path)
        return True
