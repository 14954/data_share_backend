# app.py
from apiflask import APIFlask
from werkzeug.exceptions import HTTPException
from flask_cors import CORS

from config import Config


def create_app():
    app = APIFlask(
        __name__,
        title="Data Share Client Gateway API",
        version="1.0.0",
        docs_path="/docs",
        openapi_blueprint_url_prefix="/",
    )
    app.config.from_object(Config)
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["JSON_SORT_KEYS"] = False

    app.security_schemes = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }

    CORS(
        app,
        origins=[Config.CORS_ORIGIN],
        supports_credentials=True,
        expose_headers=["Content-Disposition", "Content-Type"],
    )  # 配置跨域

    # 注册本地中转站蓝图：前端仍访问 /remote/*，请求会转发到远程 market_server。
    from routes import local_bp, proxy_bp
    app.register_blueprint(local_bp, url_prefix="/local")
    app.register_blueprint(proxy_bp, url_prefix="/remote")

    # 健康检查路由
    @app.route("/health", methods=["GET"])
    def health_check():
        return {
            "ok": True,
            "role": "data_share_backend_gateway",
            "marketServerUrl": app.config["MARKET_SERVER_URL"],
        }

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        status = err.code or 500
        return {
            "code": status,
            "message": err.name,
            "details": err.description,
        }, status

    return app


if __name__ == "__main__":
    app = create_app()
    print(f"Proxying /remote/* to {app.config['MARKET_SERVER_URL']}")
    app.run(host=app.config["APP_HOST"], port=app.config["APP_PORT"], debug=True)
