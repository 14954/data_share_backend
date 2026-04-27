# config.py
import os


class Config:
    # 允许的前端跨域源
    CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")
    # 远程数据市场服务地址。本地 data_share_backend 作为前端与 market_server 的中转站。
    MARKET_SERVER_URL = os.getenv("MARKET_SERVER_URL", "http://127.0.0.1:54321")
    MARKET_SERVER_API_PREFIX = os.getenv("MARKET_SERVER_API_PREFIX", "/api")
    # 本地中转站监听地址
    APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT = int(os.getenv("APP_PORT", "54320"))
