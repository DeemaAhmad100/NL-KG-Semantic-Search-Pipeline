"""LLM client provider resolution."""

from __future__ import annotations

import os
import shutil
import subprocess

from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from . import OllamaModelMissingError, NoLLMClientAvailableError


def _ollama_has_model(model: str) -> bool:
    """Course-provided helper."""
    if shutil.which("ollama") is None:
        return False
    try:
        out = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception:
        return False
    return any(model.split(":")[0] in line for line in out.stdout.splitlines())


def get_llm_client(model: str = "phi3:mini-4k-instruct-q4_K_M"):
    """Return a LangChain LLM client (Runnable with .invoke())."""

    # 1. OLLAMA_HOST override
    ollama_host = os.environ.get("OLLAMA_HOST")
    if ollama_host:
        return ChatOllama(model=model, base_url=ollama_host)

    # 2. Local Ollama
    if shutil.which("ollama") is not None:
        if not _ollama_has_model(model):
            raise OllamaModelMissingError(
                f"Model {model!r} not pulled. Run: ollama pull {model}"
            )
        return ChatOllama(model=model)

    # 3. OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 4. Anthropic
    if os.environ.get("ANTHROPIC_API_KEY"):
        return ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)

    # 5. Fail
    raise NoLLMClientAvailableError(
        f"No LLM provider available. Install Ollama and run: ollama pull {model}\n"
        "Or set OPENAI_API_KEY / ANTHROPIC_API_KEY."
    )