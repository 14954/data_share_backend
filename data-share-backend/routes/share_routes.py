from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from controllers.share_controller import create_share, list_my_sharing, list_shared_with_me, update_share
from models.user import User
from models.dataset import  Dataset

share_bp = Blueprint('shares', __name__)
# 创建共享
@share_bp.route('/requests', methods=['POST'])
@jwt_required()
def register():
    consumer_id = get_jwt_identity()           # 获取当前JWT中保存的用户ID
    data = request.get_json()  # 获取请求JSON数据
    dataset_id = data.get('datasetId') if data else None
    description = data.get('message') if data else None
    # 调用控制器执行注册逻辑
    status = create_share(consumer_id, dataset_id, description)
    return jsonify(status), 200

# 更新共享
@share_bp.route('/update', methods=['POST'])
@jwt_required()
def update():
    data = request.get_json()  # 获取请求JSON数据
    share_id = data.get('shareId') if data else None
    is_shared = data.get('isShared') if data else None
    # 调用控制器执行注册逻辑
    status = update_share(share_id, is_shared)
    return jsonify(status), 200

@share_bp.route('/sharing-with-others', methods=['GET'])
@jwt_required()
def list_my_sharing_route():
    provider_id = get_jwt_identity()# 获取当前JWT中保存的用户ID
    # 调用控制器执行注册逻辑
    sharing_dataset = list_my_sharing(provider_id)
    sharing_list = [ {
        "id": sd.id,
        "consumerName": User.query.get(sd.consumer_id).username if sd.consumer_id else "unknown",
        "datasetName": Dataset.query.get(sd.dataset_id).name if sd.dataset_id else "unknown",
        "request_description": sd.request_description,
        "isShared": sd.is_shared,
    } for sd in sharing_dataset ]
    return jsonify({ "sharing": sharing_list }), 200

@share_bp.route('/shared-with-me', methods=['GET'])
@jwt_required()
def list_shared_with_me_route():
    consumer_id = get_jwt_identity()# 获取当前JWT中保存的用户ID
    # 调用控制器执行注册逻辑
    shared_dataset = list_shared_with_me(consumer_id)
    shared_list = [ {
        "id": sd.id,
        "providerName": User.query.get(sd.provider_id).username if sd.provider_id else "unknown",
        "datasetName": Dataset.query.get(sd.dataset_id).name if sd.dataset_id else "unknown",
        "datasetId": sd.dataset_id
    } for sd in shared_dataset ]
    return jsonify({ "shared": shared_list }), 200
