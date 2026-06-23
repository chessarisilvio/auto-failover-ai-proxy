#!/usr/bin/env python3
"""
Auto-failover AI proxy router.
Forwards requests to local proxy if healthy, otherwise to cloud endpoint.
"""

import os
import sys
import subprocess
from flask import Flask, request, Response
import requests

app = Flask(__name__)

# Configuration via environment variables with sensible defaults
LOCAL_PROXY_HOST = os.environ.get('LOCAL_PROXY_HOST', 'localhost')
LOCAL_PROXY_PORT = os.environ.get('LOCAL_PROXY_PORT', '8090')
CLOUD_ENDPOINT = os.environ.get('CLOUD_ENDPOINT', 'https://api.openai.com/v1')
HEALTH_CHECK_SCRIPT = os.environ.get('HEALTH_CHECK_SCRIPT', './health_check.sh')
REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', '30'))

def is_local_healthy():
    """Run health_check.sh and return True if exit code 0."""
    try:
        result = subprocess.run(
            [HEALTH_CHECK_SCRIPT],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        # If health check fails, treat as unhealthy
        app.logger.warning(f"Health check failed: {e}")
        return False

def forward_request(target_url, method, headers, data, params):
    """Forward the request to target_url and return Flask Response."""
    # Remove hop-by-hop headers that should not be forwarded
    excluded_headers = ['host', 'content-length']
    forwarded_headers = {k: v for k, v in headers.items()
                         if k.lower() not in excluded_headers}

    try:
        resp = requests.request(
            method=method,
            url=target_url,
            headers=forwarded_headers,
            data=data,
            params=params,
            timeout=REQUEST_TIMEOUT,
            stream=True  # Important for large responses
        )
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Failed to forward request to {target_url}: {e}")
        return Response(f"Proxy error: {e}", status=502)

    # Build Flask response from upstream response
    response_headers = [(name, value) for (name, value) in resp.raw.headers.items()
                        if name.lower() not in excluded_headers]
    return Response(
        resp.content,
        status=resp.status_code,
        headers=response_headers
    )

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
def proxy(path):
    # Determine target based on health check
    if is_local_healthy():
        target_base = f"http://{LOCAL_PROXY_HOST}:{LOCAL_PROXY_PORT}"
        app.logger.debug(f"Routing to local proxy: {target_base}")
    else:
        target_base = CLOUD_ENDPOINT
        app.logger.debug(f"Routing to cloud endpoint: {target_base}")

    target_url = f"{target_base}/{path}"

    # Forward the request
    return forward_request(
        target_url=target_url,
        method=request.method,
        headers=request.headers,
        data=request.get_data(),
        params=request.args
    )

if __name__ == '__main__':
    # For development; in production use a proper WSGI server like gunicorn
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)