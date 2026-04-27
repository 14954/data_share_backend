import importlib
from flask import abort


def generate_provider_signed_download_url(
    objectKey: str,
    bucket: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: str,
    region: str = "ap-southeast-2",
    expires_in: int = 3600,
    endpoint_url: str = None,
):
    """Use provider STS credentials to generate a signed S3 download URL."""
    if not objectKey:
        abort(400, description="objectKey required")
    if not bucket:
        abort(400, description="bucket required")
    if not access_key_id or not secret_access_key or not session_token:
        abort(400, description="sts credentials required")

    if expires_in < 60 or expires_in > 43200:
        abort(400, description="expiresIn must be between 60 and 43200 seconds")

    try:
        boto3_module = importlib.import_module("boto3")
        s3_client = boto3_module.client(
            "s3",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            aws_session_token=session_token,
            region_name=region,
            endpoint_url=endpoint_url or None,
        )
        signed_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": objectKey,"ResponseContentDisposition":"attachment"},
            ExpiresIn=expires_in,
        )
    except Exception:
        abort(400, description="failed to generate signed url")

    return {
        "signed_url": signed_url,
        "expiresIn": expires_in,
        "objectKey": objectKey,
    }
