"""SqliteCoachRepository - trwałość coachingu (Prompt 4.4).

Implementuje `ICoachRepository`. Plan + działania zapisywane atomowo. Notatki
check-inów i komentarze outcome'ów są **szyfrowane AES-GCM** przez wstrzyknięty
`ICryptoService` - w bazie leżą jako nieczytelne BLOB-y (CLAUDE - pola wrażliwe).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from datetime import datetime
from uuid import uuid4

from application.dto.coach import (
    CheckInDTO,
    CoachActionDTO,
    CoachPlanDTO,
    OutcomeDTO,
)
from application.ports.repositories import ICoachRepository
from application.ports.security import ICryptoService
from domain.coaching import CoachPlan
from domain.common import Goal


class SqliteCoachRepository(ICoachRepository):
    def __init__(
        self,
        connection: sqlite3.Connection,
        crypto: ICryptoService,
        *,
        id_factory: Callable[[], str] = lambda: str(uuid4()),
    ) -> None:
        self._conn = connection
        self._crypto = crypto
        self._new_id = id_factory

    # --- plan ---

    def save_plan(self, plan: CoachPlan, *, created_at: datetime) -> str:
        plan_id = self._new_id()
        try:
            self._conn.execute("BEGIN")
            self._conn.execute(
                """
                INSERT INTO coach_plan(
                    id, created_at, based_on_session_id, focus_areas_json,
                    goal, daily_time_budget, escalation_flag
                ) VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    created_at.isoformat(),
                    plan.based_on_session_id,
                    json.dumps(list(plan.focus_areas)),
                    plan.goal.value,
                    plan.daily_time_budget,
                    1 if plan.escalation_flag else 0,
                ),
            )
            for akcja in plan.actions:
                self._conn.execute(
                    """
                    INSERT INTO coach_action(
                        id, plan_id, action_type, description, scheduled_date,
                        completed_date, rating
                    ) VALUES(?, ?, ?, ?, ?, NULL, NULL)
                    """,
                    (
                        self._new_id(),
                        plan_id,
                        akcja.action_type,
                        akcja.text,
                        str(akcja.day),
                    ),
                )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return plan_id

    def get_plan(self, plan_id: str) -> CoachPlanDTO | None:
        row = self._conn.execute(
            """
            SELECT id, created_at, based_on_session_id, focus_areas_json,
                   goal, daily_time_budget, escalation_flag
            FROM coach_plan WHERE id = ?
            """,
            (plan_id,),
        ).fetchone()
        if row is None:
            return None
        return self._zbuduj_plan_dto(row)

    def update_action(
        self, action_id: str, *, completed_date: str | None, rating: int | None
    ) -> None:
        try:
            self._conn.execute("BEGIN")
            self._conn.execute(
                "UPDATE coach_action SET completed_date = ?, rating = ? WHERE id = ?",
                (completed_date, rating, action_id),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def get_latest_plan(self) -> CoachPlanDTO | None:
        row = self._conn.execute(
            """
            SELECT id, created_at, based_on_session_id, focus_areas_json,
                   goal, daily_time_budget, escalation_flag
            FROM coach_plan ORDER BY created_at DESC LIMIT 1
            """
        ).fetchone()
        if row is None:
            return None
        return self._zbuduj_plan_dto(row)

    def _zbuduj_plan_dto(self, row: sqlite3.Row) -> CoachPlanDTO:
        akcje_rows = self._conn.execute(
            """
            SELECT id, action_type, description, scheduled_date,
                   completed_date, rating
            FROM coach_action WHERE plan_id = ?
            ORDER BY CAST(scheduled_date AS INTEGER)
            """,
            (row["id"],),
        ).fetchall()
        actions = [
            CoachActionDTO(
                id=a["id"],
                action_type=a["action_type"],
                description=a["description"],
                scheduled_day=int(a["scheduled_date"]),
                completed_date=a["completed_date"],
                rating=a["rating"],
            )
            for a in akcje_rows
        ]
        return CoachPlanDTO(
            id=row["id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            based_on_session_id=row["based_on_session_id"],
            goal=Goal(row["goal"]),
            daily_time_budget=row["daily_time_budget"],
            escalation_flag=bool(row["escalation_flag"]),
            focus_areas=json.loads(row["focus_areas_json"]),
            actions=actions,
        )

    # --- check-iny ---

    def save_checkin(self, checkin: CheckInDTO) -> str:
        checkin_id = checkin.id or self._new_id()
        notes_blob = (
            self._crypto.encrypt(checkin.note) if checkin.note is not None else None
        )
        try:
            self._conn.execute("BEGIN")
            self._conn.execute(
                """
                INSERT INTO coach_checkin(
                    id, plan_id, date, stress, sleep, energy, notes
                ) VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkin_id,
                    checkin.plan_id,
                    checkin.date,
                    checkin.stress,
                    checkin.sleep,
                    checkin.energy,
                    notes_blob,
                ),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return checkin_id

    def get_checkins(self, plan_id: str | None = None) -> list[CheckInDTO]:
        if plan_id is None:
            rows = self._conn.execute(
                "SELECT id, plan_id, date, stress, sleep, energy, notes "
                "FROM coach_checkin ORDER BY date"
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id, plan_id, date, stress, sleep, energy, notes "
                "FROM coach_checkin WHERE plan_id = ? ORDER BY date",
                (plan_id,),
            ).fetchall()
        return [
            CheckInDTO(
                id=r["id"],
                plan_id=r["plan_id"],
                date=r["date"],
                stress=r["stress"],
                sleep=r["sleep"],
                energy=r["energy"],
                note=self._crypto.decrypt(r["notes"]) if r["notes"] is not None else None,
            )
            for r in rows
        ]

    # --- outcome ---

    def save_outcome(self, outcome: OutcomeDTO) -> str:
        outcome_id = outcome.id or self._new_id()
        comments_blob = (
            self._crypto.encrypt(outcome.comments)
            if outcome.comments is not None
            else None
        )
        try:
            self._conn.execute("BEGIN")
            self._conn.execute(
                """
                INSERT INTO coach_outcome(
                    id, plan_id, date, perceived_burnout, comments
                ) VALUES(?, ?, ?, ?, ?)
                """,
                (
                    outcome_id,
                    outcome.plan_id,
                    outcome.date,
                    outcome.perceived_burnout,
                    comments_blob,
                ),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return outcome_id

    def get_outcomes(self, plan_id: str) -> list[OutcomeDTO]:
        rows = self._conn.execute(
            "SELECT id, plan_id, date, perceived_burnout, comments "
            "FROM coach_outcome WHERE plan_id = ? ORDER BY date",
            (plan_id,),
        ).fetchall()
        return [
            OutcomeDTO(
                id=r["id"],
                plan_id=r["plan_id"],
                date=r["date"],
                perceived_burnout=r["perceived_burnout"],
                comments=self._crypto.decrypt(r["comments"])
                if r["comments"] is not None
                else None,
            )
            for r in rows
        ]
