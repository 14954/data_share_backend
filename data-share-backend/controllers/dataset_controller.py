import os
from flask import abort, send_file
from werkzeug.utils import secure_filename

from db import database
from models.dataset import Dataset
from models.download_log import DownloadLog
from utils.preview import read_first_lines

def create_dataset(owner_id: int, name: str, description: str, domain: str, data_type: str, file_storage):
    """处理数据集上传登记"""
    # 检查必填
    if not file_storage:
        abort(400, description="file required")
    if not name:
        abort(400, description="name required")
    # 确保上传目录存在
    upload_dir = os.getenv("UPLOAD_DIR", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    # 保存文件到上传目录
    filename = secure_filename(file_storage.filename)
    file_path = os.path.join(upload_dir, f"{int(__import__('time').time())}_{filename}")
    file_storage.save(file_path)
    file_size = os.path.getsize(file_path)
    # 创建数据集记录
    dataset = Dataset(
        name=name,
        description=description or "",
        domain=domain or "general",
        data_type=data_type or "file",
        file_path=file_path,
        file_size=file_size,
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
    # 读取文件前几行内容作为预览
    preview_lines = read_first_lines(dataset.file_path, max_lines=10)
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
    """处理文件下载，记录日志并返回文件响应"""
    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        abort(404, description="not found")
    # 未上架的数据只能被拥有者下载，其他人无权限
    if not dataset.is_listed and dataset.owner_id != user_id:
        abort(403, description="not allowed")
    # 记录下载日志，增加下载计数
    log = DownloadLog(user_id=user_id, dataset_id=dataset.id)
    database.session.add(log)
    dataset.downloads += 1
    database.session.commit()
    # 发送文件
    filename = os.path.basename(dataset.file_path)
    return send_file(dataset.file_path, as_attachment=True, download_name=filename)
