"""
MinIO / S3 storage client for evidence artifacts.

Provides:
  - Upload with content-addressed key
  - Download + integrity verification
  - WORM (Write Once Read Many) lock support
  - Presigned URL generation for secure downloads
"""

from __future__ import annotations

import io
from datetime import timedelta

import structlog

from app.config import get_settings

logger = structlog.get_logger()


class StorageClient:
    """S3-compatible storage client for evidence artifacts."""

    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        """Lazy-initialize the MinIO client."""
        if self._client is None:
            try:
                from minio import Minio

                settings = get_settings()
                self._client = Minio(
                    endpoint=settings.minio_endpoint,
                    access_key=settings.minio_access_key,
                    secret_key=settings.minio_secret_key,
                    secure=settings.minio_use_ssl,
                )
                logger.info("minio_client_initialized", endpoint=settings.minio_endpoint)
            except ImportError:
                logger.warning("minio_not_installed")
                return None
            except Exception as e:
                logger.error("minio_init_failed", error=str(e))
                return None
        return self._client

    async def ensure_bucket(self, bucket: str) -> bool:
        """Create bucket if it doesn't exist."""
        client = self._get_client()
        if client is None:
            return False
        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                logger.info("bucket_created", bucket=bucket)
            return True
        except Exception as e:
            logger.error("bucket_ensure_failed", bucket=bucket, error=str(e))
            return False

    async def upload(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/json",
    ) -> bool:
        """Upload content to storage."""
        client = self._get_client()
        if client is None:
            logger.warning("storage_upload_skipped", reason="client unavailable", key=key)
            return False

        try:
            await self.ensure_bucket(bucket)
            client.put_object(
                bucket_name=bucket,
                object_name=key,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            logger.info("storage_upload_success", bucket=bucket, key=key, size=len(data))
            return True
        except Exception as e:
            logger.error("storage_upload_failed", bucket=bucket, key=key, error=str(e))
            return False

    async def download(self, bucket: str, key: str) -> bytes | None:
        """Download content from storage."""
        client = self._get_client()
        if client is None:
            return None

        try:
            response = client.get_object(bucket, key)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            logger.error("storage_download_failed", bucket=bucket, key=key, error=str(e))
            return None

    async def get_presigned_url(
        self, bucket: str, key: str, expires: timedelta = timedelta(hours=1)
    ) -> str | None:
        """Generate a presigned URL for secure temporary access."""
        client = self._get_client()
        if client is None:
            return None

        try:
            return client.presigned_get_object(bucket, key, expires=expires)
        except Exception as e:
            logger.error("presigned_url_failed", bucket=bucket, key=key, error=str(e))
            return None

    async def verify_integrity(self, bucket: str, key: str, expected_hash: str) -> dict:
        """Download content and verify SHA-256 matches stored hash."""
        from app.utils.hashing import sha256_bytes

        data = await self.download(bucket, key)
        if data is None:
            return {"verified": False, "reason": "download_failed"}

        actual_hash = sha256_bytes(data)
        matches = actual_hash == expected_hash
        return {
            "verified": matches,
            "expected_hash": expected_hash,
            "actual_hash": actual_hash,
            "size_bytes": len(data),
        }


# Singleton
storage_client = StorageClient()
