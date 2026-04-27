import os
import uuid
import importlib
from flask import abort, send_file, url_for, current_app
from werkzeug.utils import secure_filename

from config import database
from models.dataset import Dataset
from models.download_log import DownloadLog
from utils.preview import read_dataset_preview_lines


def _authorize_and_count_download(dataset_id: int, user_id: int):
    """统一下载授权、下载日志与计数逻辑"""
    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        abort(404, description="not found")

    if not dataset.is_listed and dataset.owner_id != user_id:
        abort(403, description="not allowed")

    log = DownloadLog(user_id=user_id, dataset_id=dataset.id)
    database.session.add(log)
    dataset.downloads += 1
    database.session.commit()
    return dataset


def _save_uploaded_file(file):
    filename = secure_filename(file.filename or "")
    if not filename:
        abort(400, description="filename required")

    upload_dir = current_app.config.get("UPLOAD_DIR", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    saved_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.abspath(os.path.join(upload_dir, saved_name))
    real_upload_dir = os.path.abspath(upload_dir)
    if os.path.commonpath([real_upload_dir, file_path]) != real_upload_dir:
        abort(400, description="invalid filename")

    file.save(file_path)
    object_key = os.path.join(upload_dir, saved_name).replace("\\", "/")
    return saved_name, object_key, file_path, os.path.getsize(file_path)


def _local_file_path_from_object_key(object_key):
    if not object_key:
        return None

    file_path = os.path.abspath(object_key)
    real_upload_dir = os.path.abspath(current_app.config.get("UPLOAD_DIR", "uploads"))
    if os.path.commonpath([real_upload_dir, file_path]) != real_upload_dir:
        return None
    return file_path


def generate_provider_signed_download_url(
    s3id: str,
    bucket: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: str,
    region: str = "us-east-1",
    expires_in: int = 3600,
    endpoint_url: str = None,
):
    """Use provider STS credentials to generate a signed S3 download URL."""
    if not s3id:
        abort(400, description="s3id required")
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
            Params={"Bucket": bucket, "Key": s3id,"ResponseContentDisposition":"attachment"},
            ExpiresIn=expires_in,
        )
    except Exception:
        abort(400, description="failed to generate signed url")

    return {
        "signedUrl": signed_url,
        "expiresIn": expires_in,
        "objectKey": s3id,
    }


def create_dataset(owner_id: int, name: str, description: str, domain: str, data_type: str, object_key: str = None, file_size: int = 0, file=None):
    """处理数据集登记：支持 S3 objectKey 登记，也支持本地文件上传。"""
    if not name:
        abort(400, description="name required")

    if bool(object_key) == bool(file):
        abort(400, description="provide exactly one upload source: objectKey or file")

    if file:
        _, object_key, _, saved_size = _save_uploaded_file(file)
        file_size = saved_size

    dataset = Dataset(
        name=name,
        description=description or "",
        domain=domain or "general",
        data_type=data_type or "file",
        object_key=object_key,
        file_size=file_size or 0,
        is_listed=False,
        downloads=0,
        owner_id=owner_id
    )
    database.session.add(dataset)
    database.session.commit()
    return dataset

def list_my_datasets(owner_id: int):
    """列出当前用户上传的所有数据集（我的数据）"""
    datasets = Dataset.query.filter_by(owner_id=owner_id).order_by(Dataset.id.desc()).all()
    return datasets

def list_market_datasets(domain: str = None, sort: str = None):
    """列出所有上架的数据集列表（数据市场）"""
    query = Dataset.query.filter_by(is_listed=True)
    if domain:
        query = query.filter_by(domain=domain)
    # 根据排序参数选择排序方式
    if sort == "downloads":
        query = query.order_by(Dataset.downloads.desc())
    elif sort == "size":
        query = query.order_by(Dataset.file_size.desc())
    else:
        query = query.order_by(Dataset.id.desc())
    # 最多返回200条
    datasets = query.limit(200).all()
    return datasets

def get_dataset_detail(dataset_id: int):
    """获取数据集详情和预览（仅限上架的数据）"""
    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        abort(404, description="not found")
    # 若数据集未上架，则禁止访问（即使是拥有者也不提供详情，和原逻辑保持一致）
    if not dataset.is_listed:
        abort(403, description="not listed")
    # 仅读取文本/CSV预览，失败返回空数组
    preview_lines = read_dataset_preview_lines(dataset, max_lines=10)
    return dataset, preview_lines

def toggle_listing(dataset_id: int, owner_id: int, is_listed: bool):
    """切换数据集的上架/下架状态"""
    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        abort(404, description="not found")
    if dataset.owner_id != owner_id:
        abort(403, description="not owner")
    dataset.is_listed = bool(is_listed)
    database.session.commit()
    return dataset

def download_dataset_file(dataset_id: int, user_id: int):
    """处理下载：local返回文件流，s3重定向到已登记URL"""
    dataset = _authorize_and_count_download(dataset_id, user_id)

    storage_type = (getattr(dataset, "storage_type", None) or "local").lower()
    if storage_type == "s3":
        if not getattr(dataset, "s3_url", None):
            abort(404, description="download url missing")
        return {"downloadUrl": dataset.s3_url}

    file_path = _local_file_path_from_object_key(dataset.object_key)
    if not file_path:
        abort(404, description="file missing")
    if not os.path.exists(file_path):
        abort(404, description="file not found")

    filename = os.path.basename(file_path)
    return send_file(file_path, as_attachment=True, download_name=filename)


def get_dataset_download_url(dataset_id: int, user_id: int):
    """返回下载URL，复用下载授权与计数逻辑"""
    dataset = _authorize_and_count_download(dataset_id, user_id)
    storage_type = (getattr(dataset, "storage_type", None) or "local").lower()

    if storage_type == "s3":
        if not getattr(dataset, "s3_url", None):
            abort(404, description="download url missing")
        return {"downloadUrl": dataset.s3_url, "source": "s3"}

    return {
        "downloadUrl": url_for("datasets.download_file", dataset_id=dataset.id, _external=False),
        "source": "local",
    }
