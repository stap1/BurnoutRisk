"""SqliteSurveyRepository - trwałość sesji ankiety (Prompt 3.3).

Implementuje port `ISurveyRepository`. **Zapis jest atomowy**: sesja + wszystkie
odpowiedzi + wyniki obszarów w JEDNEJ transakcji; dowolny błąd → ROLLBACK, brak
zapisu częściowego (spec §4.4). `busy_timeout` ustawia warstwa połączenia.

To jedyne miejsce z SQL dla ankiety. Nazwy obszarów (do DTO przy odczycie) bierze
z wstrzykniętej definicji. Generator identyfikatorów jest wstrzykiwany (determinizm
w testach, w produkcji UUID4).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Mapping
from datetime import datetime
from uuid import uuid4

from application.dto.survey import (
    AreaScoreDTO,
    SessionSummaryDTO,
    SurveyAnswersDTO,
    SurveyResultDTO,
)
from application.ports.repositories import ISurveyRepository
from domain.common import AreaStatus, RiskBand
from domain.survey import ScoringResult, SurveyDefinition, risk_band

APP_VERSION = "0.1.0"


class SqliteSurveyRepository(ISurveyRepository):
    def __init__(
        self,
        connection: sqlite3.Connection,
        definition: SurveyDefinition,
        *,
        id_factory: Callable[[], str] = lambda: str(uuid4()),
    ) -> None:
        self._conn = connection
        self._definition = definition
        self._new_id = id_factory

    def save_survey(
        self,
        *,
        answers: SurveyAnswersDTO,
        risk_scores: Mapping[str, int | None],
        result: ScoringResult,
        created_at: datetime,
    ) -> str:
        session_id = self._new_id()
        czas = created_at.isoformat()

        try:
            self._conn.execute("BEGIN")
            self._conn.execute(
                """
                INSERT INTO survey_session(
                    id, started_at, completed_at, total_score, risk_band,
                    top_areas_json, unrated_areas_json, app_version
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    czas,
                    czas,
                    result.total_score,
                    result.risk_band.value if result.risk_band else None,
                    json.dumps(list(result.top_areas)),
                    json.dumps(list(result.unrated_areas)),
                    APP_VERSION,
                ),
            )

            for a in answers.answers:
                self._conn.execute(
                    """
                    INSERT INTO survey_answer(
                        id, session_id, question_id, raw_answer, risk_score, skipped
                    ) VALUES(?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self._new_id(),
                        session_id,
                        a.question_id,
                        a.raw_answer,
                        risk_scores.get(a.question_id),
                        1 if a.skipped else 0,
                    ),
                )

            for area in result.area_scores:
                self._conn.execute(
                    """
                    INSERT INTO category_score(
                        id, session_id, category_id, score, status
                    ) VALUES(?, ?, ?, ?, ?)
                    """,
                    (
                        self._new_id(),
                        session_id,
                        area.category_id,
                        area.score,
                        area.status.value,
                    ),
                )

            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

        return session_id

    def get_history(self) -> list[SessionSummaryDTO]:
        rows = self._conn.execute(
            """
            SELECT id, started_at, total_score, risk_band
            FROM survey_session
            ORDER BY started_at DESC, id DESC
            """
        ).fetchall()
        return [
            SessionSummaryDTO(
                session_id=r["id"],
                created_at=datetime.fromisoformat(r["started_at"]),
                total_score=r["total_score"],
                risk_band=RiskBand(r["risk_band"]) if r["risk_band"] else None,
            )
            for r in rows
        ]

    def get_session(self, session_id: str) -> SurveyResultDTO | None:
        sesja = self._conn.execute(
            """
            SELECT id, started_at, total_score, risk_band,
                   top_areas_json, unrated_areas_json
            FROM survey_session WHERE id = ?
            """,
            (session_id,),
        ).fetchone()
        if sesja is None:
            return None

        cat_rows = self._conn.execute(
            """
            SELECT category_id, score, status FROM category_score
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchall()

        nazwy = {c.id: c.name for c in self._definition.categories}
        kolejnosc = {c.id: i for i, c in enumerate(self._definition.categories)}
        area_scores = sorted(
            (
                AreaScoreDTO(
                    category_id=r["category_id"],
                    name=nazwy.get(r["category_id"], r["category_id"]),
                    score=r["score"],
                    status=AreaStatus(r["status"]),
                    band=risk_band(r["score"]) if r["score"] is not None else None,
                )
                for r in cat_rows
            ),
            key=lambda a: kolejnosc.get(a.category_id, 99),
        )

        return SurveyResultDTO(
            session_id=sesja["id"],
            created_at=datetime.fromisoformat(sesja["started_at"]),
            total_score=sesja["total_score"],
            risk_band=RiskBand(sesja["risk_band"]) if sesja["risk_band"] else None,
            area_scores=area_scores,
            top_areas=json.loads(sesja["top_areas_json"]),
            unrated_areas=json.loads(sesja["unrated_areas_json"]),
        )
