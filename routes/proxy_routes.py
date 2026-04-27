from urllib.parse import urljoin

import requests
from apiflask import APIBlueprint
from flask import Response, abort, current_app, request


proxy_bp = APIBlueprint("proxy", __name__)

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-encoding",
    "host",
    "content-length",
}


def _forward_headers():
    return {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }


def _upstream_url(target_path: str) -> str:
    base_url = current_app.config["MARKET_SERVER_URL"].rstrip("/") + "/"
    api_prefix = current_app.config.get("MARKET_SERVER_API_PREFIX", "/remote").strip("/")
    upstream_path = "/".join(part for part in [api_prefix, target_path.lstrip("/")] if part)
    return urljoin(base_url, upstream_path)


@proxy_bp.route("/<path:target_path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@proxy_bp.route("", defaults={"target_path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def proxy(target_path):
    headers = _forward_headers()

    try:
        upstream = requests.request(
            method=request.method,
            url=_upstream_url(target_path),
            params=request.args,
            headers=headers,
            data=request.get_data(),
            stream=True,
            timeout=(5, 300),
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        abort(502, description=f"market_server unavailable: {exc}")

    response_headers = [
        (key, value)
        for key, value in upstream.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    ]

    response = Response(
        upstream.iter_content(chunk_size=8192),
        status=upstream.status_code,
        headers=response_headers,
        direct_passthrough=True,
    )
    response.call_on_close(upstream.close)
    return response
