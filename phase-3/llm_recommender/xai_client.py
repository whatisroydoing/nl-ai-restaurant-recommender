from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .models import LLMError


class LLMClient:
    def generate(self, *, model: str, messages: List[Dict[str, str]], timeout_s: float) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class XAIChatCompletionsClient(LLMClient):
    """
    Minimal XAI (Grok) Chat Completions client using stdlib HTTP.

    Env:
    - XAI_API_KEY (required for real calls)
    - XAI_BASE_URL (optional, default https://api.x.ai/v1)
    """

    api_key: Optional[str] = None
    base_url: str = "https://api.x.ai/v1"

    def generate(self, *, model: str, messages: List[Dict[str, str]], timeout_s: float) -> str:
        api_key = self.api_key or os.environ.get("XAI_API_KEY")
        if not api_key:
            raise LLMError("XAI_API_KEY is not set")

        base_url = os.environ.get("XAI_BASE_URL", self.base_url).rstrip("/")
        url = f"{base_url}/chat/completions"

        body: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
        }

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            method="POST",
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8")
            except Exception:
                detail = ""
            raise LLMError(f"XAI HTTP error {e.code}: {detail or e.reason}") from e
        except Exception as e:
            raise LLMError(f"XAI request failed: {e}") from e
        finally:
            _ = time.time() - start

        try:
            payload = json.loads(raw)
            return payload["choices"][0]["message"]["content"]
        except Exception as e:
            raise LLMError(f"Unexpected XAI response shape: {e}") from e

