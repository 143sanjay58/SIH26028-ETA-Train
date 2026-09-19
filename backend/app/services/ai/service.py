import asyncio
import random
import time
from typing import Optional, Dict, List

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

from .base import AIProvider, AIResponse, AIStreamChunk, ProviderHealth, ProviderStatus
from .nvidia import NvidiaProvider
from .gemini import GeminiProvider
from .groq import GroqProvider

logger = get_logger(__name__)


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = "closed"
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0

    @property
    def state(self) -> str:
        if self._state == "open" and self._last_failure_time:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = "half-open"
                self._half_open_calls = 0
        return self._state

    def record_success(self):
        if self._state == "half-open":
            self._half_open_calls += 1
            if self._half_open_calls >= self.half_open_max_calls:
                self._state = "closed"
                self._failure_count = 0
        elif self._state == "closed":
            self._failure_count = 0

    def record_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._state == "half-open":
            self._state = "open"
        elif self._state == "closed" and self._failure_count >= self.failure_threshold:
            self._state = "open"

    def can_execute(self) -> bool:
        return self.state != "open"


class AIService:
    def __init__(self):
        self._providers: Dict[str, AIProvider] = {}
        self._primary_provider_name: str = settings.primary_ai_provider
        self._fallback_provider_name: Optional[str] = settings.fallback_ai_provider
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return

        if settings.nvidia_api_key:
            self._providers["nvidia"] = NvidiaProvider(
                api_key=settings.nvidia_api_key,
                model=settings.nvidia_model,
                timeout=settings.ai_request_timeout,
                max_retries=settings.ai_max_retries,
            )
            self._circuit_breakers["nvidia"] = CircuitBreaker()

        if settings.gemini_api_key:
            self._providers["gemini"] = GeminiProvider(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
                timeout=settings.ai_request_timeout,
                max_retries=settings.ai_max_retries,
            )
            self._circuit_breakers["gemini"] = CircuitBreaker()

        if settings.groq_api_key:
            self._providers["groq"] = GroqProvider(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                timeout=settings.ai_request_timeout,
                max_retries=settings.ai_max_retries,
            )
            self._circuit_breakers["groq"] = CircuitBreaker()

        self._initialized = True
        logger.info("AI Service initialized", providers=list(self._providers.keys()))

    async def close(self):
        for provider in self._providers.values():
            await provider.close()

    def _get_provider_order(self) -> List[str]:
        order = []
        if self._primary_provider_name in self._providers:
            order.append(self._primary_provider_name)
        if self._fallback_provider_name and self._fallback_provider_name in self._providers:
            if self._fallback_provider_name not in order:
                order.append(self._fallback_provider_name)
        for name in self._providers:
            if name not in order:
                order.append(name)
        return order

    def _get_available_provider(self) -> Optional[AIProvider]:
        for name in self._get_provider_order():
            provider = self._providers.get(name)
            breaker = self._circuit_breakers.get(name)
            if provider and breaker and breaker.can_execute():
                if provider.health.status != ProviderStatus.UNAVAILABLE:
                    return provider
        return None

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AIResponse:
        await self.initialize()
        
        last_error = None
        for provider_name in self._get_provider_order():
            provider = self._providers.get(provider_name)
            breaker = self._circuit_breakers.get(provider_name)
            
            if not provider or not breaker:
                continue
            if not breaker.can_execute():
                logger.info("Circuit breaker open, skipping provider", provider=provider_name)
                continue
            if provider.health.status == ProviderStatus.UNAVAILABLE:
                logger.info("Provider unavailable, skipping", provider=provider_name)
                continue

            try:
                logger.info("Attempting AI generation", provider=provider_name)
                response = await provider.generate(prompt, system_prompt, temperature, max_tokens)
                breaker.record_success()
                logger.info("AI generation successful", provider=provider_name)
                return response
            except Exception as e:
                breaker.record_failure()
                last_error = e
                logger.warning(
                    "AI generation failed, trying next provider",
                    provider=provider_name,
                    error=str(e),
                    circuit_state=breaker.state,
                )
                continue

        raise Exception(f"All AI providers failed. Last error: {last_error}")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ):
        await self.initialize()
        
        last_error = None
        for provider_name in self._get_provider_order():
            provider = self._providers.get(provider_name)
            breaker = self._circuit_breakers.get(provider_name)
            
            if not provider or not breaker:
                continue
            if not breaker.can_execute():
                logger.info("Circuit breaker open, skipping provider", provider=provider_name)
                continue
            if provider.health.status == ProviderStatus.UNAVAILABLE:
                logger.info("Provider unavailable, skipping", provider=provider_name)
                continue

            try:
                logger.info("Attempting AI stream generation", provider=provider_name)
                async for chunk in provider.generate_stream(prompt, system_prompt, temperature, max_tokens):
                    yield chunk
                breaker.record_success()
                logger.info("AI stream generation successful", provider=provider_name)
                return
            except Exception as e:
                breaker.record_failure()
                last_error = e
                logger.warning(
                    "AI stream generation failed, trying next provider",
                    provider=provider_name,
                    error=str(e),
                    circuit_state=breaker.state,
                )
                continue

        raise Exception(f"All AI providers failed for streaming. Last error: {last_error}")

    async def health_check(self) -> Dict[str, ProviderHealth]:
        await self.initialize()
        results = {}
        for name, provider in self._providers.items():
            try:
                is_healthy = await provider.health_check()
                provider._health.status = ProviderStatus.HEALTHY if is_healthy else ProviderStatus.DEGRADED
            except Exception:
                provider._health.status = ProviderStatus.UNAVAILABLE
            results[name] = provider.health
        return results

    def get_provider_status(self) -> Dict[str, dict]:
        return {
            name: {
                "status": provider.health.status.value,
                "consecutive_failures": provider.health.consecutive_failures,
                "last_error": provider.health.last_error,
                "circuit_breaker_state": self._circuit_breakers.get(name, CircuitBreaker()).state,
            }
            for name, provider in self._providers.items()
        }


ai_service = AIService()