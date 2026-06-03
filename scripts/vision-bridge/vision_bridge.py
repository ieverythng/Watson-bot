#!/usr/bin/env python3
"""Vision Bridge Proxy — sits between Codex clients and LiteLLM/llama.cpp.

Architecture:
    [Codex CLI/App] → [Vision Bridge :8002 on Linux (10.88.140.135)]
                         ↓ (text-only, images described)
                    [LiteLLM :4000 on Windows (10.88.140.94)] → [llama.cpp :8080]

Codex CLI uses OpenAI's /v1/responses API which supports image_url input items.
This bridge intercepts those requests, describes images via gpt-5.4-mini
(OpenAI Codex OAuth from Hermes), replaces image_url items with text messages,
then forwards the cleaned request to LiteLLM on Windows via ZeroTier.

LiteLLM translates /v1/responses → /v1/chat/completions for llama.cpp.
"""

import base64
import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from openai import OpenAI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("vision-bridge")

# ─── Configuration ────────────────────────────────────────────────────────

# Where LiteLLM proxy lives (Windows PC via ZeroTier)
LITELLM_BASE_URL = os.environ.get(
    "VISION_BRIDGE_UPSTREAM", "http://10.88.140.94:4000/v1"
).rstrip("/")

# Local model name served by LiteLLM
LOCAL_MODEL = os.environ.get("VISION_BRIDGE_LOCAL_MODEL", "qwen36-turbo-hermes")

# Vision model for describing images (via Codex OAuth)
VISION_MODEL = os.environ.get("VISION_BRIDGE_VISION_MODEL", "gpt-5.4-mini")

# Hermes home for auth.json
HERMES_HOME = Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()
AUTH_JSON_PATH = HERMES_HOME / "auth.json"

# Port to listen on
BIND_PORT = int(os.environ.get("VISION_BRIDGE_PORT", "8002"))
BIND_HOST = os.environ.get("VISION_BRIDGE_HOST", "0.0.0.0")

# Image description cache
_IMAGE_DESC_CACHE: Dict[str, str] = {}
_IMAGE_TIME_CACHE: Dict[str, float] = {}
CACHE_TTL_SECONDS = 3600


app = FastAPI(title="Vision Bridge Proxy", version="1.0.0")


# ─── Auth & Client Setup ──────────────────────────────────────────────────

def load_codex_token() -> Optional[str]:
    """Load the OpenAI Codex OAuth access token from Hermes auth.json."""
    try:
        with open(AUTH_JSON_PATH) as f:
            data = json.load(f)
        pool = data.get("credential_pool", {})
        if not isinstance(pool, dict):
            return None

        codex_creds = pool.get("openai-codex", [])
        if isinstance(codex_creds, list) and codex_creds:
            return codex_creds[0].get("access_token")
        elif isinstance(codex_creds, dict):
            return codex_creds.get("access_token")
        return None
    except Exception as e:
        logger.error(f"Failed to load Codex token: {e}")
        return None


def build_codex_headers(access_token: str) -> Dict[str, str]:
    """Build headers for Codex OAuth endpoint (matches Hermes auxiliary_client)."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "codex_cli_rs/0.0.0 (VisionBridge)",
        "originator": "codex_cli_rs",
    }
    if isinstance(access_token, str) and access_token.strip():
        try:
            parts = access_token.split(".")
            if len(parts) >= 2:
                payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
                claims = json.loads(base64.urlsafe_b64decode(payload_b64))
                acct_id = claims.get(
                    "https://api.openai.com/auth", {}
                ).get("chatgpt_account_id")
                if isinstance(acct_id, str) and acct_id:
                    headers["ChatGPT-Account-ID"] = acct_id
        except Exception:
            pass
    return headers


def make_vision_client() -> OpenAI:
    """Create an OpenAI client pointed at the Codex OAuth endpoint."""
    token = load_codex_token()
    if not token:
        raise RuntimeError(
            "No valid Codex OAuth token found. Run 'hermes auth' to authenticate."
        )
    return OpenAI(
        api_key=token,
        base_url="https://chatgpt.com/backend-api/codex",
        default_headers=build_codex_headers(token),
    )


# ─── Image Description ────────────────────────────────────────────────────

def describe_image(b64_data: str, mime_type: str = "image/png") -> str:
    """Describe an image using gpt-5.4-mini via Codex OAuth."""
    image_hash = hashlib.sha256(b64_data.encode()).hexdigest()[:16]

    # Check cache
    if image_hash in _IMAGE_DESC_CACHE:
        cached_time = _IMAGE_TIME_CACHE.get(image_hash, 0)
        if time.time() - cached_time < CACHE_TTL_SECONDS:
            logger.debug(f"Cache hit for image {image_hash}")
            return _IMAGE_DESC_CACHE[image_hash]

    client = make_vision_client()
    prompt = (
        "Describe this image in detail. Focus on the key visual elements, "
        "any text visible, and the overall context. Be specific but concise."
    )

    try:
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64_data}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=1000,
        )
        description = response.choices[0].message.content or ""
        _IMAGE_DESC_CACHE[image_hash] = description
        _IMAGE_TIME_CACHE[image_hash] = time.time()
        logger.info(f"Image described: {description[:80]}...")
        return description
    except Exception as e:
        logger.error(f"Failed to describe image: {e}")
        return "[image description unavailable]"


def parse_image_url(url: str) -> Optional[Tuple[str, str]]:
    """Parse an image URL, returning (base64_data, mime_type) or None."""
    if url.startswith("data:"):
        parts = url.split(",", 1)
        if len(parts) == 2:
            header = parts[0]
            b64_data = parts[1]
            mime = "image/png"
            if ":" in header:
                mime = header.split(":", 1)[0].replace("data:", "")
            return (b64_data, mime)
    elif url.startswith("http://") or url.startswith("https://"):
        try:
            r = httpx.get(url, timeout=10)
            if r.status_code == 200:
                b64_data = base64.b64encode(r.content).decode()
                mime = (r.headers.get("content-type", "image/png")
                        .split(";")[0].strip())
                return (b64_data, mime)
        except Exception as e:
            logger.warning(f"Failed to fetch remote image: {e}")
    return None


# ─── Responses API Processing ─────────────────────────────────────────────

def process_responses_input(input_items: Any) -> Tuple[str, bool]:
    """Process /v1/responses input, describing images and converting to a string.

    LiteLLM's /v1/responses endpoint only accepts string `input`, not array items.
    This function extracts text from all input items, describes any images via
    gpt-5.4-mini, and returns a single concatenated string prompt.

    Returns (string_prompt, had_images).
    """
    if isinstance(input_items, str):
        # Simple string prompt — no images possible
        return input_items, False

    if not isinstance(input_items, list):
        return str(input_items), False

    parts = []
    had_images = False

    for item in input_items:
        if not isinstance(item, dict):
            continue

        item_type = item.get("type", "")

        # image_url type: {type: "image_url", content: "data:image/...;base64,..."}
        if item_type == "image_url":
            had_images = True
            content = item.get("content", "")
            parsed = parse_image_url(str(content))
            if parsed:
                b64_data, mime = parsed
                desc = describe_image(b64_data, mime)
                parts.append(f"[Image: {desc}]")
            else:
                parts.append("[image could not be processed]")

        # message type with content (string or array of blocks)
        elif item_type == "message":
            content = item.get("content", "")
            if isinstance(content, list):
                # Array of content blocks — extract text, describe images
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    block_type = block.get("type", "")
                    if block_type == "text":
                        text = block.get("text", "")
                        if text:
                            parts.append(text)
                    elif block_type in ("image_url", "image"):
                        had_images = True
                        img_val = (block.get("image_url", {})
                                  if block_type == "image_url"
                                  else block.get("image_url", {}))
                        url = (img_val.get("url", "")
                               if isinstance(img_val, dict)
                               else str(img_val))
                        parsed = parse_image_url(str(url))
                        if parsed:
                            b64_data, mime = parsed
                            desc = describe_image(b64_data, mime)
                            parts.append(f"[Image: {desc}]")
                        else:
                            parts.append("[image]")
            elif isinstance(content, str):
                if content:
                    parts.append(content)

    return "\n".join(parts), had_images


# ─── FastAPI Endpoints ────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check endpoint."""
    token_ok = load_codex_token() is not None
    return {
        "status": "ok",
        "upstream": LITELLM_BASE_URL,
        "local_model": LOCAL_MODEL,
        "vision_model": VISION_MODEL,
        "codex_token": "loaded" if token_ok else "missing",
    }


@app.get("/v1/models")
async def list_models():
    """Proxy model listing to upstream LiteLLM."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{LITELLM_BASE_URL}/models")
            return JSONResponse(
                content=resp.json(),
                status_code=resp.status_code,
            )
    except Exception as e:
        logger.error(f"Failed to fetch models from upstream: {e}")
        return JSONResponse(
            content={"data": [{"id": LOCAL_MODEL, "object": "model"}]},
            status_code=200,
        )


@app.post("/v1/responses")
async def responses(request: Request):
    """Main endpoint — intercepts /v1/responses requests, describes images,
    forwards to LiteLLM on Windows."""
    body = await request.json()

    # Process input for images
    input_val = body.get("input")
    if input_val is not None:
        processed_input, had_images = process_responses_input(input_val)
        body = dict(body)
        body["input"] = processed_input
        if had_images:
            logger.info("Images detected and described via gpt-5.4-mini")

    # Also check 'prompt' field (some Codex versions use this)
    prompt_val = body.get("prompt")
    if prompt_val is not None:
        processed_prompt, had_prompt_images = process_responses_input(prompt_val)
        if had_prompt_images:
            body = dict(body)
            body["prompt"] = processed_prompt

    # Override model if not specified
    if not body.get("model"):
        body["model"] = LOCAL_MODEL

    stream = body.get("stream", False)

    upstream_headers = {"Content-Type": "application/json"}
    auth = request.headers.get("authorization", "")
    if auth:
        upstream_headers["Authorization"] = auth

    try:
        if stream:
            async def event_stream():
                async with httpx.AsyncClient(timeout=600.0) as client:
                    async with client.stream(
                        "POST",
                        f"{LITELLM_BASE_URL}/responses",
                        json=body,
                        headers=upstream_headers,
                    ) as resp:
                        async for chunk in resp.aiter_lines():
                            if chunk:
                                yield chunk + "\n"

            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            async with httpx.AsyncClient(timeout=600.0) as client:
                resp = await client.post(
                    f"{LITELLM_BASE_URL}/responses",
                    json=body,
                    headers=upstream_headers,
                )
                return JSONResponse(
                    content=resp.json(),
                    status_code=resp.status_code,
                )

    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to upstream {LITELLM_BASE_URL}: {e}")
        return JSONResponse(
            content={
                "error": {
                    "message": f"Upstream connection failed: {LITELLM_BASE_URL} is unreachable",
                    "type": "connection_error",
                    "code": "upstream_unreachable",
                }
            },
            status_code=502,
        )
    except Exception as e:
        logger.error(f"Upstream request failed: {e}")
        return JSONResponse(
            content={
                "error": {"message": str(e), "type": "upstream_error", "code": "internal_error"}
            },
            status_code=500,
        )


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Fallback /v1/chat/completions endpoint — proxy to upstream."""
    body = await request.json()
    auth = request.headers.get("authorization", "")
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["Authorization"] = auth

    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            resp = await client.post(
                f"{LITELLM_BASE_URL}/chat/completions",
                json=body,
                headers=headers,
            )
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception as e:
        logger.error(f"Chat completions request failed: {e}")
        return JSONResponse(
            content={"error": {"message": str(e)}},
            status_code=500,
        )


# ─── Startup ──────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup."""
    logger.info("=" * 60)
    logger.info("Vision Bridge starting up")
    logger.info(f"Upstream (LiteLLM): {LITELLM_BASE_URL}")
    logger.info(f"Local model: {LOCAL_MODEL}")
    logger.info(f"Vision model: {VISION_MODEL}")

    token = load_codex_token()
    if token:
        logger.info("Codex OAuth token loaded ✓")
    else:
        logger.warning(
            "No Codex OAuth token! Vision will fall back to placeholder text. "
            "Run 'hermes auth' to authenticate."
        )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{LITELLM_BASE_URL}/models")
            if resp.status_code == 200:
                models = resp.json().get("data", [])
                logger.info(f"Upstream OK — {len(models)} model(s) available ✓")
            else:
                logger.warning(f"Upstream returned {resp.status_code}")
    except Exception as e:
        logger.warning(f"Cannot reach upstream {LITELLM_BASE_URL}: {e}")

    logger.info(f"Listening on {BIND_HOST}:{BIND_PORT}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=BIND_HOST, port=BIND_PORT, log_level="info")
