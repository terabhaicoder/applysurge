"""
Screenshot capture and S3 upload manager.

Captures page screenshots during automation workflows and uploads
them to S3 for reference and debugging.
"""

import io
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# S3 configuration
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_S3_BUCKET = os.environ.get("AWS_S3_BUCKET", "jobpilot-screenshots")
AWS_S3_REGION = os.environ.get("AWS_S3_REGION", "us-east-1")
STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local")
LOCAL_STORAGE_PATH = os.environ.get("STORAGE_LOCAL_PATH", "/app/storage")


class ScreenshotManager:
    """
    Captures page screenshots and uploads to S3 or local storage.
    Used for debugging automation workflows and providing proof of applications.
    """

    def __init__(self):
        self._s3_client = None

    def _get_s3_client(self):
        """Get or create S3 client."""
        if self._s3_client is None and STORAGE_BACKEND == "s3":
            self._s3_client = boto3.client(
                "s3",
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_S3_REGION,
            )
        return self._s3_client

    async def capture_and_upload(
        self,
        page,
        user_id: str,
        name: str,
        full_page: bool = False,
    ) -> Optional[str]:
        """
        Capture a page screenshot and upload to storage.

        Args:
            page: Playwright page instance
            user_id: User identifier for organizing screenshots
            name: Descriptive name for the screenshot
            full_page: Whether to capture the full page or just viewport

        Returns:
            URL/path of the uploaded screenshot, or None on failure
        """
        try:
            # Generate unique filename
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            filename = f"{user_id}/{timestamp}_{name}_{unique_id}.png"

            # Capture screenshot as bytes
            screenshot_bytes = await page.screenshot(
                full_page=full_page,
                type="png",
            )

            if not screenshot_bytes:
                logger.warning("Screenshot capture returned empty bytes")
                return None

            # Upload based on storage backend
            if STORAGE_BACKEND == "s3":
                url = self._upload_to_s3(filename, screenshot_bytes)
            else:
                url = self._save_to_local(filename, screenshot_bytes)

            if url:
                logger.info(f"Screenshot saved: {filename}")
            return url

        except Exception as e:
            logger.error(f"Screenshot capture/upload failed: {e}")
            return None

    def _upload_to_s3(self, key: str, data: bytes) -> Optional[str]:
        """Upload screenshot to S3 bucket."""
        try:
            s3 = self._get_s3_client()
            if not s3:
                logger.error("S3 client not available")
                return self._save_to_local(key, data)

            s3_key = f"screenshots/{key}"

            s3.put_object(
                Bucket=AWS_S3_BUCKET,
                Key=s3_key,
                Body=data,
                ContentType="image/png",
                ACL="private",
                Metadata={
                    "source": "jobpilot-automation",
                },
            )

            # Generate URL (presigned for private buckets)
            url = s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": AWS_S3_BUCKET,
                    "Key": s3_key,
                },
                ExpiresIn=604800,  # 7 days
            )

            return url

        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            # Fallback to local storage
            return self._save_to_local(key, data)
        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            return None

    def _save_to_local(self, filename: str, data: bytes) -> Optional[str]:
        """Save screenshot to local filesystem."""
        try:
            screenshots_dir = os.path.join(LOCAL_STORAGE_PATH, "screenshots")
            filepath = os.path.join(screenshots_dir, filename)

            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, "wb") as f:
                f.write(data)

            # Return relative URL path
            return f"/storage/screenshots/{filename}"

        except Exception as e:
            logger.error(f"Local save failed: {e}")
            return None

    async def capture_element(
        self,
        page,
        selector: str,
        user_id: str,
        name: str,
    ) -> Optional[str]:
        """
        Capture a screenshot of a specific element.

        Args:
            page: Playwright page instance
            selector: CSS selector for the element
            user_id: User identifier
            name: Screenshot name

        Returns:
            URL of the uploaded screenshot
        """
        try:
            element = await page.query_selector(selector)
            if not element:
                logger.warning(f"Element not found: {selector}")
                return None

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            filename = f"{user_id}/{timestamp}_{name}_{unique_id}.png"

            screenshot_bytes = await element.screenshot(type="png")

            if STORAGE_BACKEND == "s3":
                return self._upload_to_s3(filename, screenshot_bytes)
            else:
                return self._save_to_local(filename, screenshot_bytes)

        except Exception as e:
            logger.error(f"Element screenshot failed: {e}")
            return None

    def delete_screenshot(self, url: str) -> bool:
        """Delete a screenshot from storage."""
        try:
            if STORAGE_BACKEND == "s3" and "s3" in url:
                # Extract key from URL
                key = url.split(f"{AWS_S3_BUCKET}/")[-1].split("?")[0]
                s3 = self._get_s3_client()
                if s3:
                    s3.delete_object(Bucket=AWS_S3_BUCKET, Key=key)
                    return True
            else:
                # Local file
                filepath = url.replace("/storage/", f"{LOCAL_STORAGE_PATH}/")
                if os.path.exists(filepath):
                    os.remove(filepath)
                    return True
        except Exception as e:
            logger.error(f"Delete screenshot failed: {e}")
        return False

    async def cleanup_old_screenshots(self, user_id: str, max_age_days: int = 30):
        """Clean up screenshots older than max_age_days."""
        try:
            if STORAGE_BACKEND == "s3":
                s3 = self._get_s3_client()
                if not s3:
                    return

                prefix = f"screenshots/{user_id}/"
                response = s3.list_objects_v2(Bucket=AWS_S3_BUCKET, Prefix=prefix)

                if "Contents" not in response:
                    return

                cutoff = datetime.now(timezone.utc).timestamp() - (max_age_days * 86400)
                keys_to_delete = []

                for obj in response["Contents"]:
                    if obj["LastModified"].timestamp() < cutoff:
                        keys_to_delete.append({"Key": obj["Key"]})

                if keys_to_delete:
                    s3.delete_objects(
                        Bucket=AWS_S3_BUCKET,
                        Delete={"Objects": keys_to_delete},
                    )
                    logger.info(f"Deleted {len(keys_to_delete)} old screenshots for user {user_id}")

            else:
                # Local cleanup
                import glob
                import time

                user_dir = os.path.join(LOCAL_STORAGE_PATH, "screenshots", user_id)
                if not os.path.exists(user_dir):
                    return

                cutoff = time.time() - (max_age_days * 86400)
                for filepath in glob.glob(os.path.join(user_dir, "*.png")):
                    if os.path.getmtime(filepath) < cutoff:
                        os.remove(filepath)

        except Exception as e:
            logger.error(f"Screenshot cleanup failed: {e}")
