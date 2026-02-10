# config.py
import os

class Config:
    # JWT 秘钥，用于签署JWT令牌
    JWT_SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret")
    # 数据库连接URI，使用SQLAlchemy的mysql+pymysql驱动格式
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "1")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "data_share_test")
    SQLALCHEMY_DATABASE_URI = (f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭修改跟踪，提高性能
    # 上传文件目录
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    # 允许的前端跨域源
    CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")
