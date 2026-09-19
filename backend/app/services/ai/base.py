from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
from dataclasses import dataclass
from enum import Enum


class ProviderStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class AIResponse:
    content: str
    model: str
    provider: str
    usage: Optional[dict] = None
    finish_reason: Optional[str] = None


@dataclass
class AIStreamChunk:
    content: str
    is_final: bool = False
    finish_reason: Optional[str] = None


@dataclass
class ProviderHealth:
    name: str
    status: ProviderStatus
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    last_success: Optional[float] = None


class AIProvider(ABC):
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self._health = ProviderHealth(name=self.provider_name, status=ProviderStatus.HEALTHY)

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    def health(self) -> ProviderHealth:
        return self._health

    def _update_health(self, success: bool, error: Optional[str] = None):
        import time
        if success:
            self._health.status = ProviderStatus.HEALTHY
            self._health.consecutive_failures = 0
            self._health.last_success = time.time()
            self._health.last_error = None
        else:
            self._health.consecutive_failures += 1
            self._health.last_error = error
            if self._health.consecutive_failures >= 3:
                self._health.status = ProviderStatus.UNAVAILABLE
            elif self._health.consecutive_failures >= 1:
                self._health.status = ProviderStatus.DEGRADED

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AIResponse:
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncGenerator[AIStreamChunk, None]:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass