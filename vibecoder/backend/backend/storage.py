from __future__ import annotations

import io
import os
from datetime import timedelta
from pathlib import Path
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

from .config import get_settings

_settings = get_settings()
_client = Minio(
    _settings.object_storage_endpoint.replace("http://", "").replace("https://", ""),
    access_key=_settings.object_storage_access_key,
    secret_key=_settings.object_storage_secret_key,
    secure=_settings.object_storage_endpoint.startswith("https://"),
)
_fallback_root = Path(os.getenv("VIBECODER_ARTIFACTS", "./artifacts"))


def ensure_bucket() -> None:
    try:
        if not _client.bucket_exists(_settings.object_storage_bucket):
            _client.make_bucket(_settings.object_storage_bucket)
    except Exception:
        _fallback_root.mkdir(parents=True, exist_ok=True)


def put_bytes(path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    ensure_bucket()
    try:
        file_obj: BinaryIO = io.BytesIO(data)
        file_obj.seek(0)
        _client.put_object(
            _settings.object_storage_bucket,
            path,
            file_obj,
            length=len(data),
            content_type=content_type,
        )
    except Exception:
        target = _fallback_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return path


def get_bytes(path: str) -> bytes:
    ensure_bucket()
    try:
        obj = _client.get_object(_settings.object_storage_bucket, path)
    except Exception:
        target = _fallback_root / path
        if not target.exists():
            raise FileNotFoundError(path)
        return target.read_bytes()

    try:
        data = obj.read()
    finally:
        obj.close()
        obj.release_conn()
    return data


def get_signed_url(path: str, expires: int = 3600) -> str:
    ensure_bucket()
    try:
        return _client.get_presigned_url(
            "GET",
            _settings.object_storage_bucket,
            path,
            expires=timedelta(seconds=expires),
        )
    except (S3Error, Exception):
        target = _fallback_root / path
        if not target.exists():
            raise FileNotFoundError(path)
        return target.resolve().as_uri()
