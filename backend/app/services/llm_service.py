import json
import re

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.core.config import get_settings


class LLMNotConfiguredError(RuntimeError):
    pass


class LLMGenerationError(RuntimeError):
    pass


class TutorReply(BaseModel):
    reply: str = Field(min_length=1, max_length=500)


class DiscussionTutorReply(BaseModel):
    feedback: str = Field(min_length=1, max_length=400)
    reply: str = Field(min_length=1, max_length=500)
    needs_improvement: bool = False


SYSTEM_PROMPT = """You are AI Lingua, a kind tutor for a child learning beginner French.
Keep every reply short, safe, and age-appropriate.
Encourage first, then correct gently if needed.
Use simple French with a little English support only when helpful.
Avoid adult topics, politics, scary content, and unsafe open-ended conversation.
Ask at most one simple follow-up question.
Do not include hidden reasoning or thinking text.
Reply with only the tutor message text."""

THINK_BLOCK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
CODE_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


class OllamaTutorService:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
        auth_token: str | None = None,
        timeout_seconds: float = 60,
    ) -> None:
        settings = get_settings()
        self.base_url = (base_url if base_url is not None else settings.ollama_base_url) or ""
        self.model = (model if model is not None else settings.ollama_model) or ""
        self.auth_token = auth_token if auth_token is not None else settings.ollama_auth_token
        self.timeout_seconds = timeout_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.model)

    async def reply_to_child(
        self,
        *,
        child_text: str,
        topic: str | None = None,
        difficulty: str = "beginner",
    ) -> TutorReply:
        if not self.is_configured:
            raise LLMNotConfiguredError("Ollama is not configured. Set OLLAMA_BASE_URL and OLLAMA_MODEL.")

        user_prompt = (
            "/no_think\n"
            f"Difficulty: {difficulty}\n"
            f"Topic: {topic or 'general beginner French'}\n"
            f"Child said: {child_text}\n"
            "Reply as the tutor."
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.4,
                "num_predict": 180,
            },
        }
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url.rstrip('/')}/api/chat",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMGenerationError(str(exc)) from exc

        message = response.json().get("message", {})
        content = message.get("content", "")
        return parse_tutor_reply(content)

    async def answer_child_question(
        self,
        *,
        question: str,
        difficulty: str = "beginner",
    ) -> TutorReply:
        user_prompt = (
            "/no_think\n"
            f"Difficulty: {difficulty}\n"
            f"Child question: {question}\n"
            "Answer the child's question in simple beginner French. "
            "Keep it short, warm, and age-appropriate. "
            "If the question is not about French learning, still answer safely in French. "
            "Reply only in French."
        )
        content = await self._chat(user_prompt=user_prompt, num_predict=160)
        return parse_tutor_reply(content)

    async def start_discussion(
        self,
        *,
        topic: str,
        difficulty: str = "beginner",
    ) -> TutorReply:
        user_prompt = (
            "/no_think\n"
            f"Difficulty: {difficulty}\n"
            f"Topic: {topic}\n"
            "Start a child-friendly French discussion. Ask one simple relevant question."
        )
        content = await self._chat(user_prompt=user_prompt, num_predict=120)
        return parse_tutor_reply(content)

    async def continue_discussion(
        self,
        *,
        topic: str,
        child_text: str,
        turn_index: int,
        improvement_attempts: int,
        difficulty: str = "beginner",
    ) -> DiscussionTutorReply:
        user_prompt = (
            "/no_think\n"
            f"Difficulty: {difficulty}\n"
            f"Topic: {topic}\n"
            f"Discussion turn: {turn_index}\n"
            f"Recent improvement attempts on the same idea: {improvement_attempts}\n"
            f"Child answer transcript: {child_text}\n"
            "Assess correctness and likely pronunciation from the transcript. "
            "Give one brief feedback sentence. If there is a small improvement to try and fewer than 2 improvement attempts have happened, set needs_improvement true and ask for one short retry. "
            "Otherwise set needs_improvement false and ask the next simple relevant question so the discussion keeps moving. "
            "Return only JSON with this shape: {\"feedback\":\"...\",\"reply\":\"...\",\"needs_improvement\":false}."
        )
        content = await self._chat(user_prompt=user_prompt, num_predict=180)
        return parse_discussion_reply(content)

    async def _chat(self, *, user_prompt: str, num_predict: int) -> str:
        if not self.is_configured:
            raise LLMNotConfiguredError("Ollama is not configured. Set OLLAMA_BASE_URL and OLLAMA_MODEL.")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.4,
                "num_predict": num_predict,
            },
        }
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url.rstrip('/')}/api/chat",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMGenerationError(str(exc)) from exc

        return response.json().get("message", {}).get("content", "")


def parse_tutor_reply(content: str) -> TutorReply:
    cleaned = clean_model_content(content)
    if not cleaned:
        return TutorReply(reply="Bien essaye ! Dis encore une phrase en francais.")

    parsed = parse_json_object(cleaned)
    if parsed is not None:
        try:
            return TutorReply.model_validate(parsed)
        except ValidationError as exc:
            raise LLMGenerationError("Ollama returned an invalid tutor response.") from exc

    fallback = cleaned.splitlines()[0].strip().strip('"')
    try:
        return TutorReply(reply=fallback)
    except ValidationError as exc:
        raise LLMGenerationError("Ollama returned an invalid tutor response.") from exc


def parse_discussion_reply(content: str) -> DiscussionTutorReply:
    cleaned = clean_model_content(content)
    parsed = parse_json_object(cleaned) if cleaned else None
    if parsed is not None:
        try:
            return DiscussionTutorReply.model_validate(parsed)
        except ValidationError:
            pass

    fallback = parse_tutor_reply(cleaned).reply if cleaned else "Bien essaye !"
    return DiscussionTutorReply(
        feedback="Merci pour ta reponse.",
        reply=fallback,
        needs_improvement=False,
    )


def clean_model_content(content: str) -> str:
    without_thinking = THINK_BLOCK_PATTERN.sub("", content).strip()
    fenced_match = CODE_FENCE_PATTERN.search(without_thinking)
    if fenced_match:
        return fenced_match.group(1).strip()
    return without_thinking


def parse_json_object(content: str) -> dict | None:
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, char in enumerate(content):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(content[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    return None
