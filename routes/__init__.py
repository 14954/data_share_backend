from .local_routes import local_bp
from .proxy_routes import proxy_bp

__all__ = ["proxy_bp", "local_bp"]  # 导出本地中转站蓝图
