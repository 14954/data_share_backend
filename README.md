# data_share_backend

客户端本地中转站。前端 `data_share_frontend` 仍然访问本机后端，例如 `http://localhost:54320`，本服务再把 `/remote/*` 请求转发到远程 `market_server`。

## 角色边界

- `data_share_frontend`：客户端界面。
- `data_share_backend`：客户端本地网关，不保存业务数据，不直接访问数据库。
- `market_server`：远程数据市场服务端，保留原有认证、数据集、共享审批、下载等全部业务逻辑。

## 启动

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
set MARKET_SERVER_URL=http://服务器IP:54321
python app.py
```

默认配置：

- 本地网关地址：`http://127.0.0.1:54320`
- 远程市场服务：`http://127.0.0.1:54321`
- 前端跨域源：`http://localhost:5173`

## 环境变量

- `MARKET_SERVER_URL`：远程 `market_server` 根地址，例如 `http://192.168.1.10:54321`
- `MARKET_SERVER_API_PREFIX`：远程 API 前缀，默认 `/remote`
- `APP_HOST`：本地网关监听地址，默认 `127.0.0.1`
- `APP_PORT`：本地网关监听端口，默认 `54320`
- `CORS_ORIGIN`：允许访问本地网关的前端地址，默认 `http://localhost:5173`

## API

前端路径不变，仍访问：

- `POST /remote/auth/register`
- `POST /remote/auth/login`
- `POST /remote/datasets/upload`
- `GET /remote/datasets/mine`
- `GET /remote/datasets/market`
- `GET /remote/datasets/<dataset_id>`
- `PATCH /remote/datasets/<dataset_id>/listing`
- `GET /remote/datasets/<dataset_id>/download`
- `GET /remote/datasets/<dataset_id>/download-url`
- `POST /remote/shares/requests`
- `PATCH /remote/shares/<share_id>`
- `GET /remote/shares/sharing-with-others`
- `GET /remote/shares/shared-with-me`
- `GET /remote/shares/requests-by-me`

这些请求会由本地网关原样转发给远程 `market_server`。
