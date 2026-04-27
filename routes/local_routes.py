from urllib.parse import urljoin

import requests
from apiflask import APIBlueprint
from flask import abort, current_app, request

from controllers import generate_provider_signed_download_url


local_bp = APIBlueprint("local", __name__)


def _market_url(path: str) -> str:
    base_url = current_app.config["MARKET_SERVER_URL"].rstrip("/") + "/"
    return urljoin(base_url, path.lstrip("/"))


@local_bp.post("/generate_url")
def generate_url():
    data = request.get_json(silent=True) or {}
    share_id = data.get("shareId")
    if not share_id:
        abort(400, description="shareId required")

    generated = generate_provider_signed_download_url(
        objectKey=data.get("objectKey"),
        bucket=data.get("bucket"),
        access_key_id=data.get("access_key_id"),
        secret_access_key=data.get("secret_access_key"),
        session_token=data.get("session_token"),
        region=data.get("region") or "ap-southeast-2",
        expires_in=int(data.get("expires_in") or 3600),
        endpoint_url=data.get("endpoint_url") or data.get("endpoint"),
    )

    headers = {}
    auth_header = request.headers.get("Authorization")
    if auth_header:
        headers["Authorization"] = auth_header

    try:
        upstream = requests.post(
            _market_url("/remote/shares/update"),
            json={
                "shareId": share_id,
                "signed_url": generated["signed_url"],
            },
            headers=headers,
            timeout=(5, 30),
        )
    except requests.RequestException as exc:
        abort(502, description=f"failed to update market_server share: {exc}")

    if upstream.status_code >= 400:
        try:
            payload = upstream.json()
            message = payload.get("message") or payload.get("details") or upstream.text
        except ValueError:
            message = upstream.text
        abort(upstream.status_code, description=message or "market_server update failed")

    return {
        "status": "success",
        "shareId": share_id,
        **generated,
    }
