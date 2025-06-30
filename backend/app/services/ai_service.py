from __future__ import annotations

"""Light-weight wrapper around the LLM provider used for meal suggestions.

The REST layer depends only on the public ``get_ai_suggestion`` coroutine to
remain decoupled from any concrete provider (OpenAI, Azure, etc.).  This stub
tries to call OpenAI if the environment variable ``OPENAI_API_KEY`` is set; if
not, it falls back to a deterministic mock response so the API can boot
without credentials.
"""

from typing import Any, Dict

from ..utils.logger import logger

__all__ = ["get_ai_suggestion"]


async def _openai_chat_completion(prompt: str) -> str | None:  # pragma: no cover
    """Attempt to obtain a completion from OpenAI if configured.

    This runs in a best-effort mode: failures are logged and silently ignored
    so the caller can still receive a placeholder response.
    """

    import os

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        import openai

        # Lazily set key to avoid touching env at import time.
        openai.api_key = api_key

        response = await openai.ChatCompletion.acreate(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a diabetes nutrition expert."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content  # type: ignore[index]
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("OpenAI request failed: %s", exc)
        return None


async def get_ai_suggestion(prompt: str) -> Dict[str, Any]:
    """Return an AI-generated meal suggestion for *prompt*.

    The return type is normalised to ``{"text": <string>}`` so that the REST
    layer can evolve independently of the chosen provider.
    """

    suggestion_text = await _openai_chat_completion(prompt)
    if not suggestion_text:
        suggestion_text = (
            "(Debug) Example meal suggestion for demonstration purposes based "
            "on the following prompt:\n" + prompt[:200]
        )

    return {"text": suggestion_text} 