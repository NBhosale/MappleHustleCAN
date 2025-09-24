import os
from uuid import uuid4

import boto3
from fastapi import UploadFile

USE_S3 = os.getenv("USE_S3", "false").lower() == "true"

# S3 Config
S3_BUCKET = os.getenv("S3_BUCKET")
S3_REGION = os.getenv("S3_REGION")
S3_KEY = os.getenv("S3_KEY")
S3_SECRET = os.getenv("S3_SECRET")

if USE_S3:
    s3_client = boto3.client(
        "s3",
        region_name=S3_REGION,
        aws_access_key_id=S3_KEY,
        aws_secret_access_key=S3_SECRET,
    )


async def save_file(file: UploadFile, folder: str = "uploads") -> str:
    """
    Save file locally or to S3.
    Returns path/URL.
    """
    ext = file.filename.split(".")[-1]
    filename = f"{uuid4()}.{ext}"

    if USE_S3:
        s3_client.upload_fileobj(file.file, S3_BUCKET, f"{folder}/{filename}")
        return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{folder}/{filename}"

    else:
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)
        with open(filepath, "wb") as f:
            f.write(await file.read())
        return filepath
