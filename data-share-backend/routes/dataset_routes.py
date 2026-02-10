from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from controllers.dataset_controller import (
    create_dataset, list_my_datasets, list_market_datasets,
    get_dataset_detail, toggle_listing, download_dataset_file
)
from models.user import User

dataset_bp = Blueprint('datasets', __name__)

# 上传登记数据集 
@dataset_bp.route('/', methods=['POST'])
@dataset_bp.route('', methods=['POST'])
@jwt_required()  # JWT保护，必须登录
def upload_dataset():
    current_user_id = get_jwt_identity()           # 获取当前JWT中保存的用户ID
    # 从请求中获取表单数据和文件
    name = request.form.get('name')
    description = request.form.get('description')
    domain = request.form.get('domain')
    data_type = request.form.get('dataType')
    file = request.files.get('file')
    # 调用控制器处理上传逻辑
    dataset = create_dataset(current_user_id, name, description, domain, data_type, file)
    # 返回创建的数据集对象
    return jsonify({ "dataset": {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "domain": dataset.domain,
        "dataType": dataset.data_type,
        "fileSize": dataset.file_size,
        "isListed": dataset.is_listed,
        "downloads": dataset.downloads,
        "ownerId": dataset.owner_id,
        "createdAt": dataset.id    # 这里简化用ID代替创建时间
    }}), 200

# 获取我的数据集列表
@dataset_bp.route('/mine', methods=['GET'])
@jwt_required()
def my_datasets():
    current_user_id = get_jwt_identity()
    datasets = list_my_datasets(current_user_id)
    # 将结果转换为可序列化列表
    owned_list = [ {
        "id": ds.id,
        "name": ds.name,
        "description": ds.description,
        "domain": ds.domain,
        "dataType": ds.data_type,
        "fileSize": ds.file_size,
        "isListed": ds.is_listed,
        "downloads": ds.downloads,
        "ownerId": ds.owner_id,
        "createdAt": ds.id  # 同上简化处理
    } for ds in datasets ]
    return jsonify({ "owned": owned_list }), 200

# 数据市场列表 (对应 Express GET /api/datasets/market)
@dataset_bp.route('/market', methods=['GET'])
def market_list():
    domain = request.args.get('domain')
    sort = request.args.get('sort')
    datasets = list_market_datasets(domain, sort)
    market_list = [ {
        "id": ds.id,
        "name": ds.name,
        "description": ds.description,
        "domain": ds.domain,
        "dataType": ds.data_type,
        "fileSize": ds.file_size,
        "isListed": ds.is_listed,
        "downloads": ds.downloads,
        "ownerId": ds.owner_id,
        "createdAt": ds.id
    } for ds in datasets ]
    return jsonify({ "list": market_list }), 200

# 数据集详情 + 预览 (对应 Express GET /api/datasets/:id)
@dataset_bp.route('/<int:dataset_id>', methods=['GET'])
def dataset_detail(dataset_id):
    dataset, preview_lines = get_dataset_detail(dataset_id)
    return jsonify({
        "dataset": {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "domain": dataset.domain,
            "dataType": dataset.data_type,
            "fileSize": dataset.file_size,
            "downloads": dataset.downloads,
            "isListed": dataset.is_listed,
            "ownerName": User.query.get(dataset.owner_id).username if dataset.owner_id else "unknown",
        },
        "previewLines": preview_lines
    }), 200

# 切换上架状态 (对应 Express PATCH /api/datasets/:id/listing)
@dataset_bp.route('/<int:dataset_id>/listing', methods=['PATCH'])
@jwt_required()
def set_listing(dataset_id):
    current_user_id = get_jwt_identity()
    # 获取请求 JSON 中的新状态
    body = request.get_json()
    is_listed = body.get('isListed') if body else None
    updated = toggle_listing(dataset_id, current_user_id, is_listed)
    return jsonify({ "dataset": {
        "id": updated.id,
        "isListed": updated.is_listed
    }}), 200

# 数据下载 (对应 Express GET /api/datasets/:id/download)
@dataset_bp.route('/<int:dataset_id>/download', methods=['GET'])
@jwt_required()
def download_file(dataset_id):
    current_user_id = get_jwt_identity()
    # 控制器直接返回 send_file 响应
    return download_dataset_file(dataset_id, current_user_id)
