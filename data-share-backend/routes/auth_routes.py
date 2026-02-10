from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token

from controllers.auth_controller import register_user, authenticate_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()  # 获取请求JSON数据
    username = data.get('username') if data else None
    password = data.get('password') if data else None
    # 调用控制器执行注册逻辑
    user_info = register_user(username, password)
    return jsonify(user_info), 200

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username') if data else None
    password = data.get('password') if data else None
    # 验证用户名密码
    user = authenticate_user(username, password)
    # 生成JWT令牌，有效期7天，载荷包含用户id（作为身份）和用户名
    access_token = create_access_token(identity=user.id, additional_claims={"username": user.username}, expires_delta=False)
    # 返回令牌和用户信息
    return jsonify({
        "token": access_token,
        "user": { "id": user.id, "username": user.username }
    }), 200
