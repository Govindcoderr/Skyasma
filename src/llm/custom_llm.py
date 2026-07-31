from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

import requests
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from config import settings


_Q0_PROMPT_TEMPLATE = (
    "<|start|>system<|message|>{system_prompt}<|end|>"
    "<|start|>user<|message|>{user_message}<|end|>"
    "<|start|>assistant"
)


class Q0CustomLLM(BaseChatModel):
    """
    LangChain-compatible chat model wrapping the Q0 generate_stream HTTP endpoint.
    Used for plain (non-tool-calling) agents: Supervisor, Planner, Responder.
    """

    model_name: str = "gpt-oss-120b"
    api_url: str = settings.Q0_API_URL
    max_tokens: int = 1024
    temperature: float = 0.2
    top_p: float = 1.0
    timeout: int = 60

    @property
    def _llm_type(self) -> str:
        return "q0_custom"

    @staticmethod
    def _messages_to_prompt(messages: List[BaseMessage]) -> str:
        system_parts, conversation_parts = [], []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_parts.append(msg.content)
            elif isinstance(msg, HumanMessage):
                conversation_parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                conversation_parts.append(f"Assistant: {msg.content}")
            else:
                role = getattr(msg, "type", "user")
                conversation_parts.append(f"{role.capitalize()}: {msg.content}")

        system_prompt = "\n\n".join(system_parts) or "You are a helpful assistant."
        user_message = "\n\n".join(conversation_parts)

        return _Q0_PROMPT_TEMPLATE.format(system_prompt=system_prompt, user_message=user_message)

    def _build_payload(self, prompt: str) -> Dict[str, Any]:
        return {
            "text_input": prompt,
            "parameters": {
                "stream": True,
                "return_num_input_tokens": True,
                "return_num_output_tokens": True,
            },
            "sampling_parameters": json.dumps({
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
            }),
        }

    @staticmethod
    def _text_from_chunk(chunk: Dict[str, Any]) -> str:
        if "text_output" in chunk:
            return chunk["text_output"]

        outputs = chunk.get("outputs", [])
        if outputs and isinstance(outputs, list):
            return outputs[0].get("text", "")

        choices = chunk.get("choices", [])
        if choices and isinstance(choices, list):
            first = choices[0]
            delta = first.get("delta", {})
            if delta:
                return delta.get("content", "")
            return first.get("text") or first.get("message", {}).get("content", "") or ""

        return ""

    def _read_stream(self, resp: requests.Response) -> Tuple[str, Dict[str, int]]:
        collected: List[str] = []

        for raw_line in resp.iter_lines(decode_unicode=True):
            if not raw_line:
                continue

            line = raw_line.strip()
            if line.startswith("data:"):
                line = line[len("data:"):].strip()
            if line == "[DONE]":
                break

            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue

            if chunk.get("error"):
                raise RuntimeError(f"Q0 model error: {chunk['error']}")

            fragment = self._text_from_chunk(chunk)
            if fragment:
                collected.append(fragment)

        return "".join(collected), {}

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        prompt = self._messages_to_prompt(messages)
        payload = self._build_payload(prompt)

        try:
            resp = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
                stream=True,
            )
            resp.raise_for_status()
            text, usage = self._read_stream(resp)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Q0CustomLLM request failed: {e}") from e

        message = AIMessage(content=text or "")
        return ChatResult(generations=[ChatGeneration(message=message)])

    async def _agenerate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._generate, messages, stop)

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "api_url": self.api_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }