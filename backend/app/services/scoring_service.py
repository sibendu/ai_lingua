from difflib import SequenceMatcher
import re
import unicodedata

from app.schemas.practice import PracticeScore


WORD_PATTERN = re.compile(r"[a-z0-9']+")


def normalize_text(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return ascii_value.lower().replace("’", "'").strip()


def tokenize(value: str) -> list[str]:
    return WORD_PATTERN.findall(normalize_text(value))


class ScoringService:
    def score(self, target: str, transcript: str) -> PracticeScore:
        target_words = tokenize(target)
        transcript_words = tokenize(transcript)

        if not target_words:
            return PracticeScore(
                score=0,
                label="needs_help",
                feedback="Let's pick a phrase and try again.",
                missing_words=[],
                extra_words=transcript_words,
            )

        word_ratio = SequenceMatcher(None, target_words, transcript_words).ratio()
        char_ratio = SequenceMatcher(None, normalize_text(target), normalize_text(transcript)).ratio()
        score = round(((word_ratio * 0.65) + (char_ratio * 0.35)) * 100)

        missing_words = [word for word in target_words if word not in transcript_words]
        extra_words = [word for word in transcript_words if word not in target_words]
        label = self._label(score)
        feedback = self._feedback(label, missing_words)

        return PracticeScore(
            score=max(0, min(100, score)),
            label=label,
            feedback=feedback,
            missing_words=missing_words,
            extra_words=extra_words,
        )

    def _label(self, score: int) -> str:
        if score >= 90:
            return "excellent"
        if score >= 70:
            return "good"
        if score >= 45:
            return "try_again"
        return "needs_help"

    def _feedback(self, label: str, missing_words: list[str]) -> str:
        if label == "excellent":
            return "Excellent! That sounded very close."
        if label == "good":
            return "Good job. Try it once more for a smoother sound."
        if missing_words:
            return f"Nice try. Listen for: {', '.join(missing_words[:3])}."
        return "Nice try. Say it slowly once more."
