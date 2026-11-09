"""
Abstract Base Agent Class.

Provides unified inference orchestration, OpenRouter API calling with retries,
model fallback hierarchy, timeout handling, and deterministic fallback execution.
"""

import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
import httpx

from backend.app.config import get_settings
from backend.app.schemas.agent import AgentExecutionMeta
from backend.app.schemas.analysis import DeterministicAnalysisPayload
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


class BaseAgent(ABC):
    """
    Abstract Base Class for all 7 Specialized AI Agents.
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    @abstractmethod
    def run(self, payload: DeterministicAnalysisPayload, **kwargs) -> Any:
        """
        Execute the agent logic. Must be implemented by each specialized agent.
        """
        pass

    @abstractmethod
    def generate_fallback(self, payload: DeterministicAnalysisPayload, **kwargs) -> Any:
        """
        Rule-based deterministic fallback executed when LLM inference is disabled,
        unreachable, or rate-limited. Guarantees zero system downtime.
        """
        pass

    def _call_openrouter(
        self,
        prompt: str,
        system_prompt: str,
        model: Optional[str] = None,
    ) -> Optional[str]:
        """
        Send inference request to OpenRouter API with retry logic and fallback models.
        """
        api_key = settings.OPENROUTER_API_KEY.strip()
        if not api_key:
            logger.info(f"[{self.agent_name}] No OpenRouter API key found. Using deterministic fallback.")
            return None

        primary_model = model or settings.DEFAULT_LLM_MODEL
        fallback_model = settings.FALLBACK_LLM_MODEL
        models_to_try = [primary_model, fallback_model]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/multi-agent-bi",
            "X-Title": settings.APP_NAME,
        }

        for model_id in models_to_try:
            body = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            }

            for attempt in range(1, settings.MAX_RETRIES + 1):
                try:
                    logger.info(f"[{self.agent_name}] Calling LLM '{model_id}' (attempt {attempt}/{settings.MAX_RETRIES})...")
                    with httpx.Client(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
                        response = client.post(
                            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                            headers=headers,
                            json=body,
                        )

                    if response.status_code == 200:
                        data = response.json()
                        content = data["choices"][0]["message"]["content"]
                        logger.info(f"[{self.agent_name}] LLM response successfully received from '{model_id}'.")
                        return content
                    elif response.status_code in [429, 502, 503, 504]:
                        logger.warning(
                            f"[{self.agent_name}] API rate limited or server busy (status {response.status_code}). Backing off..."
                        )
                        time.sleep(attempt * 1.5)
                        continue
                    else:
                        logger.warning(
                            f"[{self.agent_name}] LLM error {response.status_code}: {response.text[:200]}"
                        )
                        break
                except Exception as e:
                    logger.warning(f"[{self.agent_name}] HTTP connection error on attempt {attempt}: {e}")
                    time.sleep(attempt * 1.0)

        logger.warning(f"[{self.agent_name}] All LLM attempts exhausted. Transitioning to deterministic fallback.")
        return None

    def _parse_json_response(self, raw_text: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Safely clean and parse JSON returned from LLM.
        """
        if not raw_text:
            return None
        text = raw_text.strip()
        # Strip markdown fences if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except Exception as e:
            logger.warning(f"[{self.agent_name}] Failed to parse JSON from LLM: {e}")
            return None

    def create_meta(
        self,
        start_time: float,
        model_used: str = "deterministic-rule-engine",
        fallback: bool = False,
    ) -> AgentExecutionMeta:
        """Generate execution metadata record."""
        elapsed = round(time.time() - start_time, 3)
        return AgentExecutionMeta(
            agent_name=self.agent_name,
            status="completed" if not fallback else "fallback",
            execution_time_seconds=elapsed,
            model_used=model_used,
            fallback_used=fallback,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

