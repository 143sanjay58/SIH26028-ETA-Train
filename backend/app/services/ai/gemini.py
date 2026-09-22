import asyncio
import random
import time
from typing import AsyncGenerator, Optional

import httpx
from backend.app.core.logging import get_logger

from .base import AIProvider, AIResponse, AIStreamChunk, ProviderHealth, ProviderStatus

logger = get_logger(__name__)


class GeminiProvider(AIProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        super().__init__(api_key, model, base_url, timeout, max_retries)
        self.client: Optional[httpx.AsyncClient] = None

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _get_client(self) -> httpx.AsyncClient:
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=10.0),
            )
        return self.client

    async def close(self):
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            self.client = None

    def _is_retryable_error(self, status_code: int, error: Exception) -> bool:
        if status_code in (429, 500, 502, 503, 504):
            return True
        if isinstance(error, (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError)):
            return True
        return False

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                client = self._get_client()
                params = {"key": self.api_key}
                if "params" in kwargs:
                    params.update(kwargs.pop("params"))
                response = await client.request(method, url, params=params, **kwargs)
                
                if response.status_code == 200:
                    self._update_health(True)
                    return response
                
                if not self._is_retryable_error(response.status_code, None):
                    self._update_health(False, f"HTTP {response.status_code}")
                    response.raise_for_status()
                
                logger.warning(
                    "Gemini request failed, retrying",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    status_code=response.status_code,
                )
                
            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                last_exception = e
                logger.warning(
                    "Gemini request error, retrying",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e),
                )
            except httpx.HTTPStatusError as e:
                if not self._is_retryable_error(e.response.status_code, e):
                    self._update_health(False, f"HTTP {e.response.status_code}")
                    raise
                last_exception = e
                logger.warning(
                    "Gemini HTTP error, retrying",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    status_code=e.response.status_code,
                )
            
            if attempt < self.max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 0.5)
                logger.info("Waiting before retry", wait_time=wait_time)
                await asyncio.sleep(wait_time)
        
        self._update_health(False, str(last_exception) if last_exception else "Max retries exceeded")
        raise last_exception or Exception("Max retries exceeded")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AIResponse:
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": system_prompt}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        try:
            url = f"/models/{self.model}:generateContent"
            response = await self._request_with_retry("POST", url, json=payload)
            data = response.json()
            
            candidates = data.get("candidates", [])
            if not candidates:
                raise Exception("No candidates in Gemini response")
            
            content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            finish_reason = candidates[0].get("finishReason")
            usage = data.get("usageMetadata")

            return AIResponse(
                content=content,
                model=self.model,
                provider=self.provider_name,
                usage=usage,
                finish_reason=finish_reason,
            )
        except Exception as e:
            logger.error("Gemini generate failed", error=str(e))
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncGenerator[AIStreamChunk, None]:
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": system_prompt}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        client = self._get_client()
        try:
            url = f"/models/{self.model}:streamGenerateContent"
            params = {"key": self.api_key, "alt": "sse"}
            
            async with client.stream("POST", url, params=params, json=payload, timeout=self.timeout) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    self._update_health(False, f"HTTP {response.status_code}: {error_text.decode()}")
                    raise httpx.HTTPStatusError(
                        f"Gemini stream error: {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                self._update_health(True)
                
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    
                    data_str = line[6:].strip()
                    try:
                        chunk_data = json.loads(data_str)
                        candidates = chunk_data.get("candidates", [])
                        if candidates:
                            content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            finish_reason = candidates[0].get("finishReason")
                            
                            if content:
                                yield AIStreamChunk(content=content, finish_reason=finish_reason)
                            if finish_reason:
                                yield AIStreamChunk(content="", is_final=True, finish_reason=finish_reason)
                    except json.JSONDecodeError:
                        continue
                        
        except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
            self._update_health(False, str(e))
            logger.error("Gemini stream connection error", error=str(e))
            raise
        except httpx.HTTPStatusError as e:
            if self._is_retryable_error(e.response.status_code, e):
                self._update_health(False, f"HTTP {e.response.status_code}")
            raise
        except Exception as e:
            self._update_health(False, str(e))
            logger.error("Gemini stream error", error=str(e))
            raise

    async def health_check(self) -> bool:
        try:
            payload = {
                "contents": [{"role": "user", "parts": [{"text": "ping"}]}],
                "generationConfig": {"maxOutputTokens": 5},
            }
            url = f"/models/{self.model}:generateContent"
            response = await self._request_with_retry("POST", url, json=payload)
            return response.status_code == 200
        except Exception as e:
            logger.warning("Gemini health check failed", error=str(e))
            return False


import json