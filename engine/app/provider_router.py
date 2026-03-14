"""V5 Provider Router — Abstraction layer cho V5 cost routing.

Tách riêng khỏi providers.py (V4 VoiceRouter, TranscriptionRouter) để tránh conflict.
Dùng cho V5.5 Cost Router policy engine.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskType(str, Enum):
    SCRIPT = "script"
    TTS = "tts"
    STT = "stt"
    FOOTAGE = "footage"
    IMAGE = "image"
    RESEARCH = "research"
    TREND = "trend"
    MODERATION = "moderation"
    EMBEDDING = "embedding"


class QualityMode(str, Enum):
    BUDGET = "budget"
    BALANCED = "balanced"
    PREMIUM = "premium"


@dataclass
class ProviderResult:
    success: bool
    data: Any = None
    error: str = ""
    provider: str = ""
    model: str = ""
    tokens_used: int = 0
    duration_ms: int = 0
    cost_estimate: float = 0.0
    cache_hit: bool = False
    metadata: dict = field(default_factory=dict)


class BaseProviderAdapter(ABC):
    name: str = "unknown"
    task_types: list[TaskType] = []

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    async def execute(self, task_type: TaskType, params: dict[str, Any]) -> ProviderResult: ...

    def supports(self, task_type: TaskType) -> bool:
        return task_type in self.task_types


@dataclass
class RoutingPolicy:
    quality_mode: QualityMode = QualityMode.BALANCED
    monthly_budget: float = 100.0
    prefer_local: bool = True
    fallback_enabled: bool = True
    task_overrides: dict[str, list[str]] = field(default_factory=dict)


class CostRouter:
    """Routes tasks to appropriate providers based on policy."""

    def __init__(self):
        self._adapters: dict[str, BaseProviderAdapter] = {}
        self._default_chains: dict[TaskType, list[str]] = {}

    def register(self, adapter: BaseProviderAdapter) -> None:
        self._adapters[adapter.name] = adapter

    def set_default_chain(self, task_type: TaskType, names: list[str]) -> None:
        self._default_chains[task_type] = names

    def get_chain(self, task_type: TaskType, policy: RoutingPolicy | None = None) -> list[str]:
        if policy and task_type.value in policy.task_overrides:
            return policy.task_overrides[task_type.value]
        return self._default_chains.get(task_type, [])

    async def route(
        self, task_type: TaskType, params: dict[str, Any],
        policy: RoutingPolicy | None = None, channel_name: str = "",
    ) -> ProviderResult:
        chain = self.get_chain(task_type, policy)
        for name in chain:
            adapter = self._adapters.get(name)
            if not adapter or not adapter.is_available() or not adapter.supports(task_type):
                continue
            start = time.monotonic()
            try:
                result = await adapter.execute(task_type, params)
                result.provider = name
                result.duration_ms = int((time.monotonic() - start) * 1000)
                if result.success:
                    return result
            except Exception:
                continue
        return ProviderResult(success=False, error=f"All providers failed for {task_type.value}: tried {chain}")

    def list_adapters(self) -> list[dict[str, Any]]:
        return [
            {"name": a.name, "available": a.is_available(), "tasks": [t.value for t in a.task_types]}
            for a in self._adapters.values()
        ]
