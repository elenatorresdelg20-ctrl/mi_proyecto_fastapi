import time
import asyncio
from functools import lru_cache
from typing import Any, Dict, Optional

import httpx

try:
    from transformers import pipeline as hf_pipeline_loader
except Exception:
    hf_pipeline_loader = None

from ..core.settings import AI_PROVIDER, AI_API_URL, AI_API_KEY, AI_TIMEOUT, AI_MAX_CONCURRENCY, COST_PER_1K_TOKENS
from ..core.db import SessionLocal
from concurrent.futures import ThreadPoolExecutor

EXECUTOR = ThreadPoolExecutor(max_workers=int(4))
_ai_semaphore = asyncio.Semaphore(AI_MAX_CONCURRENCY)


class AIClient:
    def __init__(self):
        self.provider = AI_PROVIDER

    async def explain(self, prompt: str, max_tokens: int = 300) -> Dict[str, Any]:
        start = time.time()
        async with _ai_semaphore:
            try:
                if self.provider == "cheap_api":
                    res_text = await self._call_cheap_api(prompt, max_tokens)
                    latency = time.time() - start
                    return {"text": res_text, "latency": latency, "model": "cheap_api", "cost_estimate": self._estimate_cost(len(prompt.split()), max_tokens), "confidence": 0.85}
                elif self.provider == "hf_local":
                    res_text = await self._call_hf_local(prompt, max_tokens)
                    latency = time.time() - start
                    return {"text": res_text, "latency": latency, "model": "hf_local", "cost_estimate": 0.0, "confidence": 0.80}
                else:
                    raise RuntimeError("Proveedor IA no soportado")
            except Exception as e:
                latency = time.time() - start
                return {"text": "", "latency": latency, "model": self.provider, "cost_estimate": 0.0, "confidence": 0.0, "error": str(e)}

    async def _call_cheap_api(self, prompt: str, max_tokens: int) -> str:
        if not AI_API_URL or not AI_API_KEY:
            raise RuntimeError("AI_API_URL o AI_API_KEY no configurados")
        payload = {"prompt": prompt, "max_tokens": max_tokens}
        headers = {"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=AI_TIMEOUT) as client:
            r = await client.post(AI_API_URL, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            return data.get("text") or data.get("result") or data.get("output") or ""

    async def _call_hf_local(self, prompt: str, max_tokens: int) -> str:
        if not hf_pipeline_loader:
            raise RuntimeError("Transformers no disponible para hf_local")
        from app.main import HF_LOCAL_PIPELINE  # type: ignore
        if HF_LOCAL_PIPELINE is None:
            raise RuntimeError("HF pipeline no inicializada")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(EXECUTOR, lambda: HF_LOCAL_PIPELINE(prompt, max_length=max_tokens)[0].get("generated_text", ""))

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        total_tokens = input_tokens + output_tokens
        return (total_tokens / 1000.0) * COST_PER_1K_TOKENS


# Simple in-memory cache util
_in_memory_cache: Dict[str, str] = {}

def cache_get(key: str) -> Optional[str]:
    return _in_memory_cache.get(key)

def cache_set(key: str, value: str):
    _in_memory_cache[key] = value
    if len(_in_memory_cache) > 2048:
        try:
            first_key = next(iter(_in_memory_cache))
            del _in_memory_cache[first_key]
        except StopIteration:
            pass
