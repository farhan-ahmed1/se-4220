"""Google Cloud Storage upload helper. Uploaded objects are made publicly
readable so we can render them via a plain <img src="..."> tag without
generating signed URLs."""

import os
import uuid
from google.cloud import storage

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _client():
    # On App Engine, default credentials are picked up automatically.
    # Locally, GOOGLE_APPLICATION_CREDENTIALS points at gcp-key.json.
    return storage.Client()


def upload_file(file_storage) -> str:
    """Upload a Werkzeug FileStorage and return its public URL."""
    bucket_name = os.environ["GCS_BUCKET"]
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    object_name = f"listings/{uuid.uuid4().hex}.{ext}"

    bucket = _client().bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_file(
        file_storage,
        content_type=file_storage.mimetype or f"image/{ext}",
    )
    # Bucket should have public read, but mark the object too in case bucket
    # uses fine-grained access.
    try:
        blob.make_public()
    except Exception:
        pass
    return blob.public_url
