"""SqliteEducationRepository - trwałość postępu edukacyjnego (Prompt 5.3)."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from application.dto.education import EducationProgressDTO
from application.ports.repositories import IEducationRepository


class SqliteEducationRepository(IEducationRepository):
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def get_progress(self, topic_id: str) -> EducationProgressDTO | None:
        row = self._conn.execute(
            "SELECT topic_id, first_viewed_at, last_viewed_at, quiz_score "
            "FROM education_progress WHERE topic_id = ?",
            (topic_id,),
        ).fetchone()
        if row is None:
            return None
        return EducationProgressDTO(
            topic_id=row["topic_id"],
            first_viewed_at=datetime.fromisoformat(row["first_viewed_at"]),
            last_viewed_at=datetime.fromisoformat(row["last_viewed_at"]),
            quiz_score=row["quiz_score"],
        )

    def upsert_progress(self, progress: EducationProgressDTO) -> None:
        try:
            self._conn.execute("BEGIN")
            self._conn.execute(
                """
                INSERT INTO education_progress(
                    topic_id, first_viewed_at, last_viewed_at, quiz_score
                ) VALUES(?, ?, ?, ?)
                ON CONFLICT(topic_id) DO UPDATE SET
                    last_viewed_at = excluded.last_viewed_at,
                    quiz_score = excluded.quiz_score
                """,
                (
                    progress.topic_id,
                    progress.first_viewed_at.isoformat(),
                    progress.last_viewed_at.isoformat(),
                    progress.quiz_score,
                ),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
