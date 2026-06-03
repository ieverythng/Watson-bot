#!/usr/bin/env python3
"""
Vision Proxy — transparent interceptor between Codex CLI and llama.cpp.

Sits between Codex CLI and the LiteLLM proxy. When Codex sends a request
containing image blocks (image_url with base64), this proxy:
  1. Extracts each image's base64 data
  2. Sends it to gpt-5.4-mini via ChatGPT OAuth (Codex endpoint) for description
  3. Replaces the image block with a text description in the message content
  4. Forwards the text-only request to llama.cpp via LiteLLM

Architecture:
  Codex CLI → vision_proxy (:8083) → gpt-5.4-mini (for images) + llama.cpp (for text)

The proxy uses Hermes' existing OpenAI OAuth credentials from ~/.hermes/auth.json
and the Cloudflare header pattern from auxiliary_client.py to authenticate with
the ChatGPT Codex endpoint for vision calls.

Usage:
  python3 vision_proxy.py [--port 8083] [--backend http://10.88.140.94:4000/v1]

Environment:
  VISION_PROXY_PORT     — override port (default 8083)
  VISION_PROXY_BACKEND  — override backend URL (default LiteLLM on ZeroTier)
"""

import base64
import hashlib
import hmac
import http.client
import io
import json
import logging
import os
import sys
import textwrap
import time
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_PORT = 8083
DEFAULT_BACKEND = "http://10.88.140.94:4000/v1"
HERMES_HOME = Path.home() / ".hermes"
AUTH_JSON = HERMES_HOME / "auth.json"

# gpt-5.4-mini on the ChatGPT Codex endpoint
VISION_MODEL = "gpt-5.4-mini"
CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [vision_proxy] %(levelname)s: %(message)s",
)
logger = logging.getLogger("vision_proxy")

# ---------------------------------------------------------------------------
# Auth helpers (mirrors Hermes auxiliary_client.py pattern)
# ---------------------------------------------------------------------------


def load_auth_credentials() -> Optional[Dict[str, str]]:
    """Load access_token and account_id from Hermes auth.json."""
    try:
        with open(AUTH_JSON) as f:
            auth = json.load(f)

        # Walk credential_pool for openai-codex
        pool = auth.get("credential_pool", {}).get("openai-codex", [])
        if not pool:
            logger.error("No openai-codex credentials in auth.json")
            return None

        # Pick the first valid credential
        for cred in pool:
            token = cred.get("access_token", "")
            if token and len(token) > 20:
                account_id = cred.get("account_id", "")
                if not account_id:
                    # Try to extract from providers section
                    providers = auth.get("providers", {}).get("openai-codex", {})
                    tokens = providers.get("tokens", {})
                    account_id = tokens.get("account_id", "")
                return {
                    "access_token": token,
                    "account_id": account_id,
                }

        logger.error("No valid access_token found in credential pool")
        return None
    except Exception as e:
        logger.error("Failed to load auth.json: %s", e)
        return None


def decode_jwt_account_id(access_token: str) -> Optional[str]:
    """Extract chatgpt_account_id from JWT payload."""
    try:
        parts = access_token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload_b64))
        acct = claims.get("https://api.openai.com/auth", {}).get(
            "chatgpt_account_id"
        )
        return acct if isinstance(acct, str) and acct else None
    except Exception:
        return None


def codex_headers(access_token: str) -> Dict[str, str]:
    """Build Cloudflare-compatible headers for ChatGPT Codex endpoint."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "codex_cli_rs/0.0.0 (vision_proxy)",
        "originator": "codex_cli_rs",
    }
    acct_id = decode_jwt_account_id(access_token)
    if acct_id:
        headers["ChatGPT-Account-ID"] = acct_id
    return headers


# ---------------------------------------------------------------------------
# Vision description via gpt-5.4-mini
# ---------------------------------------------------------------------------

_vision_cache: Dict[str, str] = {}  # sha256(base64) -> description


def describe_image(base64_data: str, access_token: str) -> str:
    """Send image to gpt-5.4-mini and return a text description."""
    # Cache key from the base64 content
    cache_key = hashlib.sha256(base64_data.encode()).hexdigest()
    if cache_key in _vision_cache:
        logger.debug("Vision cache hit for image")
        return _vision_cache[cache_key]

    prompt = (
        "Describe this image concisely but thoroughly. Include key visual elements, "
        "text content, layout, colors, and any notable details. Be specific enough "
        "that someone who cannot see the image can understand what it shows."
    )

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_data}"},
                },
            ]},
        ],
        "max_tokens": 1024,
    }

    headers = codex_headers(access_token)

    try:
        resp = requests.post(
            f"{CODEX_BASE_URL}/chat/completions",
            json=payload,
            headers=headers,
            timeout=60,
        )
        if resp.status_code == 401:
            logger.warning(
                "Vision call got 401 — OAuth token may be stale. "
                "Run `hermes auth` to refresh."
            )
            return "[image: unable to describe — auth error]"

        resp.raise_for_status()
        data = resp.json()
        description = data["choices"][0]["message"]["content"]

        _vision_cache[cache_key] = description
        logger.info("Image described (%.40s...): %s", base64_data, description[:80])
        return description

    except requests.exceptions.RequestException as e:
        logger.error("Vision call failed: %s", e)
        return f"[image: description failed — {e}]"


# ---------------------------------------------------------------------------
# Message processing
# ---------------------------------------------------------------------------


def has_image_content(messages: List[Dict[str, Any]]) -> bool:
    """Check if any message contains image_url blocks."""
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            continue
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "image_url":
                    return True
    return False


def extract_and_replace_images(
    messages: List[Dict[str, Any]], access_token: str
) -> List[Dict[str, Any]]:
    """Replace image_url blocks with text descriptions from gpt-5.4-mini."""
    processed = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            processed.append(msg)
            continue

        if not isinstance(content, list):
            processed.append(msg)
            continue

        new_parts = []
        for part in content:
            if not isinstance(part, dict):
                new_parts.append(part)
                continue

            if part.get("type") == "image_url":
                image_url_obj = part.get("image_url", {})
                url = (
                    image_url_obj.get("url", "")
                    if isinstance(image_url_obj, dict)
                    else str(image_url_obj)
                )

                # Extract base64 data
                b64_data = None
                if url.startswith("data:"):
                    # data:image/png;base64,XXXXX
                    comma = url.find(",")
                    if comma >= 0:
                        b64_data = url[comma + 1:]
                elif url.startswith("base64:"):
                    b64_data = url[7:]

                if b64_data:
                    description = describe_image(b64_data, access_token)
                    new_parts.append({
                        "type": "text",
                        "text": f"[Image: {description}]",
                    })
                    logger.info("Replaced image with description")
                else:
                    # URL-based image — try to fetch and describe
                    new_parts.append({
                        "type": "text",
                        "text": f"[Image at: {url}]",
                    })
            else:
                new_parts.append(part)

        processed.append({**msg, "content": new_parts})

    return processed


# ---------------------------------------------------------------------------
# HTTP proxy server
# ---------------------------------------------------------------------------


class VisionProxy:
    """Thin HTTP proxy that intercepts /chat/completions and strips images."""

    def __init__(self, port: int, backend_url: str):
        self.port = port
        self.backend_url = backend_url.rstrip("/")
        self.auth = load_auth_credentials()
        if not self.auth:
            logger.error(
                "Cannot start: no valid OAuth credentials found. "
                "Run `hermes auth` to authenticate."
            )
            sys.exit(1)

    def handle_request(self, method: str, path: str, body: bytes, headers: Dict) -> tuple:
        """Process a request and return (status, response_headers, response_body)."""
        # Parse path
        parsed = urllib.parse.urlparse(path)
        pathname = parsed.path

        # --- Passthrough endpoints ---
        if pathname == "/v1/models":
            return self._proxy_request(method, path, body, headers)

        if pathname == "/v1/chat/completions":
            return self._handle_chat_completions(body, headers)

        # Everything else: proxy to backend
        return self._proxy_request(method, path, body, headers)

    def _handle_chat_completions(self, body: bytes, headers: Dict) -> tuple:
        """Intercept chat/completions, describe images, forward to backend."""
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return 400, {"Content-Type": "application/json"}, json.dumps({"error": "invalid json"})

        messages = payload.get("messages", [])

        # Check for images
        if not has_image_content(messages):
            # No images — forward directly to backend
            logger.debug("No images in request, forwarding directly")
            return self._forward_to_backend(payload, headers)

        # Images detected — describe them
        logger.info("Images detected in request, describing via gpt-5.4-mini...")
        processed_messages = extract_and_replace_images(messages, self.auth["access_token"])

        # Build forwarded payload
        forwarded = dict(payload)
        forwarded["messages"] = processed_messages

        # Log what we're sending
        logger.info("Forwarding text-augmented request to backend")
        return self._forward_to_backend(forwarded, headers)

    def _forward_to_backend(self, payload: Dict, original_headers: Dict) -> tuple:
        """Forward a (possibly modified) request to the LiteLLM backend."""
        fwd_headers = {
            "Content-Type": "application/json",
        }
        # Pass through auth if present
        auth = original_headers.get("Authorization") or original_headers.get("authorization")
        if auth:
            fwd_headers["Authorization"] = auth

        try:
            resp = requests.post(
                f"{self.backend_url}/v1/chat/completions",
                json=payload,
                headers=fwd_headers,
                timeout=300,
                stream=True,
            )

            # Check if client wanted streaming
            payload_str = json.dumps(payload)
            want_stream = "stream" in payload_str and '"stream": true' in payload_str.replace(" ", "")

            if want_stream and resp.status_code == 200:
                # Return SSE stream
                return self._stream_response(resp)
            else:
                # Non-streaming: read full response
                content = resp.content
                return (
                    resp.status_code,
                    {"Content-Type": "application/json"},
                    content,
                )

        except requests.exceptions.RequestException as e:
            logger.error("Backend request failed: %s", e)
            return 502, {"Content-Type": "application/json"}, json.dumps({
                "error": f"backend error: {e}"
            })

    def _stream_response(self, resp) -> tuple:
        """For streaming responses, we buffer and return as SSE."""
        # For simplicity, read the full stream and return non-streamed.
        # A proper SSE proxy would need async handling.
        content = b""
        for chunk in resp.iter_content(chunk_size=4096):
            content += chunk
        return 200, {"Content-Type": "application/json"}, content

    def _proxy_request(self, method: str, path: str, body: bytes, headers: Dict) -> tuple:
        """Proxy a request directly to the backend without modification."""
        url = f"{self.backend_url}{path}"
        try:
            resp = requests.request(
                method, url, data=body, headers=headers, timeout=60
            )
            return resp.status_code, {"Content-Type": resp.headers.get("Content-Type", "application/octet-stream")}, resp.content
        except requests.exceptions.RequestException as e:
            logger.error("Proxy request failed: %s", e)
            return 502, {"Content-Type": "application/json"}, json.dumps({
                "error": f"proxy error: {e}"
            })


def run_server(port: int, backend_url: str):
    """Run the vision proxy using http.server."""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    proxy = VisionProxy(port, backend_url)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b""
            headers_dict = dict(self.headers)
            status, resp_headers, resp_body = proxy.handle_request(
                "POST", self.path, body, headers_dict
            )
            self.send_response(status)
            for k, v in resp_headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp_body if isinstance(resp_body, bytes) else resp_body.encode())

        def do_GET(self):
            headers_dict = dict(self.headers)
            status, resp_headers, resp_body = proxy.handle_request(
                "GET", self.path, b"", headers_dict
            )
            self.send_response(status)
            for k, v in resp_headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp_body if isinstance(resp_body, bytes) else resp_body.encode())

        def log_message(self, format, *args):
            # Suppress default access logs
            pass

    server = HTTPServer(("0.0.0.0", port), Handler)
    logger.info("Vision proxy listening on port %d", port)
    logger.info("Backend: %s", backend_url)
    logger.info("Auth: %s", "OK" if proxy.auth else "MISSING")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down")
        server.server_close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Vision Proxy for Codex CLI + llama.cpp")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on")
    parser.add_argument("--backend", default=DEFAULT_BACKEND, help="Backend LiteLLM URL")
    args = parser.parse_args()

    port = int(os.environ.get("VISION_PROXY_PORT", str(args.port)))
    backend = os.environ.get("VISION_PROXY_BACKEND", args.backend) or DEFAULT_BACKEND

    run_server(port, backend)


if __name__ == "__main__":
    main()
