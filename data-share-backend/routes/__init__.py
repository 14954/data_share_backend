from .auth_routes import auth_bp
from .dataset_routes import dataset_bp
from .share_routes import share_bp

__all__ = ["auth_bp", "dataset_bp", "share_bp"]  # 导出蓝图对象列表，供 app.py 导入注册
