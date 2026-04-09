from __future__ import annotations

import os
from time import perf_counter
from typing import Any

import httpx

from elbench.providers.base import ModelClient
from elbench.schemas.evaluation import GenerationRequest, ModelResponse


class OpenAICompatibleClient(ModelClient):
    def __init__(self, provider_config, model_config) -> None:
        super().__init__(provider_config, model_config)
        timeout = model_config.timeout or provider_config.default_timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def generate(self, sample, request: GenerationRequest) -> ModelResponse:
        if not self.model_config.api_base:
            raise ValueError(f"Model {self.model_config.model_id} missing api_base")
        url = self.model_config.api_base.rstrip("/") + self.provider_config.endpoint_path
        headers = dict(self.provider_config.headers)
        api_key_env = self.model_config.api_key_env
        if api_key_env:
            api_key = os.getenv(api_key_env)
            if not api_key:
                raise ValueError(f"Environment variable {api_key_env} is not set")
            headers["Authorization"] = f"Bearer {api_key}"
        headers.setdefault("Content-Type", "application/json")

        payload = self._build_payload(request)
        start = perf_counter()
        response = await self._client.post(url, headers=headers, json=payload)
        latency_ms = (perf_counter() - start) * 1000
        response.raise_for_status()
        data = response.json()
        return ModelResponse(
            text=self._extract_text(data),
            raw_payload=data,
            usage=data.get("usage", {}),
            latency_ms=latency_ms,
            status_code=response.status_code,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def _build_payload(self, request: GenerationRequest) -> dict[str, Any]:
        messages = []
        supports_system = (
            self.model_config.supports_system_prompt
            if self.model_config.supports_system_prompt is not None
            else self.provider_config.capabilities.supports_system_prompt
        )
        if request.system_prompt and supports_system:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        payload: dict[str, Any] = {
            "model": self.model_config.model_name,
            "messages": messages,
            "stream": request.stream,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.reasoning is not None:
            payload["reasoning"] = request.reasoning
        payload.update(self.model_config.provider_kwargs)
        payload.update(request.provider_kwargs)
        return payload

    def _extract_text(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, list):
            return "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        return str(content)

