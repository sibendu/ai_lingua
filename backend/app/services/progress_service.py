from collections import defaultdict
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.db.models import Attempt, PracticeItem
from app.schemas.dashboard import (
    ChildDashboardResponse,
    ParentDashboardResponse,
    RecentAttemptSummary,
    WeakTopicSummary,
)


class ProgressService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def child_dashboard(self, *, family_id: str, child_id: str) -> ChildDashboardResponse:
        attempts = self._attempts(family_id=family_id, child_id=child_id)
        today = datetime.now(UTC).date()
        attempts_today = sum(1 for attempt in attempts if attempt.created_at.date() == today)
        average_score = self._average_score(attempts)
        words_practiced = sum(len(attempt.target_text.split()) for attempt in attempts)
        stars = sum(self._stars_for_score(attempt.score) for attempt in attempts)
        recent_wins = [
            f"{attempt.target_text} ({attempt.score})"
            for attempt in attempts[:5]
            if attempt.score >= 70
        ]

        return ChildDashboardResponse(
            family_id=family_id,
            child_id=child_id,
            stars=stars,
            words_practiced=words_practiced,
            attempts_today=attempts_today,
            total_attempts=len(attempts),
            average_score=average_score,
            recent_wins=recent_wins,
        )

    def parent_dashboard(self, *, family_id: str, child_id: str) -> ParentDashboardResponse:
        attempts = self._attempts(family_id=family_id, child_id=child_id)
        item_topics = self._item_topics(attempts)
        topic_scores: dict[str, list[int]] = defaultdict(list)
        for attempt in attempts:
            topic = item_topics.get(attempt.practice_item_id, "unknown")
            topic_scores[topic].append(attempt.score)

        weak_topics = [
            WeakTopicSummary(
                topic=topic,
                attempts=len(scores),
                average_score=round(sum(scores) / len(scores), 1),
            )
            for topic, scores in topic_scores.items()
            if scores
        ]
        weak_topics.sort(key=lambda item: item.average_score)

        return ParentDashboardResponse(
            family_id=family_id,
            child_id=child_id,
            total_attempts=len(attempts),
            average_score=self._average_score(attempts),
            weak_topics=weak_topics[:5],
            recent_attempts=[
                RecentAttemptSummary(
                    attempt_id=attempt.id,
                    practice_item_id=attempt.practice_item_id,
                    topic=item_topics.get(attempt.practice_item_id),
                    target_text=attempt.target_text,
                    transcript=attempt.transcript,
                    score=attempt.score,
                    feedback=attempt.feedback,
                    created_at=attempt.created_at,
                )
                for attempt in attempts[:10]
            ],
        )

    def _attempts(self, *, family_id: str, child_id: str) -> list[Attempt]:
        return list(
            self.session.exec(
                select(Attempt)
                .where(Attempt.family_id == family_id, Attempt.child_id == child_id)
                .order_by(Attempt.created_at.desc())
            )
        )

    def _item_topics(self, attempts: list[Attempt]) -> dict[str, str]:
        item_ids = {attempt.practice_item_id for attempt in attempts}
        if not item_ids:
            return {}

        items = self.session.exec(
            select(PracticeItem).where(PracticeItem.id.in_(item_ids))
        )
        return {item.id: item.topic for item in items}

    def _average_score(self, attempts: list[Attempt]) -> float | None:
        if not attempts:
            return None
        return round(sum(attempt.score for attempt in attempts) / len(attempts), 1)

    def _stars_for_score(self, score: int) -> int:
        if score >= 90:
            return 3
        if score >= 70:
            return 2
        if score >= 45:
            return 1
        return 0
