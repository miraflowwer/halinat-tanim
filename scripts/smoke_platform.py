"""Smoke-test the authenticated Phase 5 plan flow through the API."""

import asyncio
import secrets
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import httpx

import services.api.app as api_module
from services.api.auth import (
    AuthenticatedSession,
    AuthResult,
    AuthUser,
    hash_session_secret,
)
from services.api.config import SESSION_LIFETIME
from services.api.platform_repository import PlanRecord
from services.engine.config import load_engine_config
from services.engine.models import (
    CropRecord,
    GeographyRecord,
    ReferenceRecord,
)
from services.engine.models import (
    PlanRecord as EnginePlanRecord,
)
from services.engine.service import RiskService


class SmokeAuthStore:
    def __init__(self):
        self.user = AuthUser(
            1,
            "Smoke Farmer",
            "farmer.demo@tanim.local",
            "farmer",
            "en",
            True,
        )
        self.sessions: dict[str, AuthenticatedSession] = {}

    def login(self, *, email: str, password: str) -> AuthResult:
        if email.lower() != self.user.email or password != "phase5-smoke-password":
            raise AssertionError("The smoke flow used unexpected login details.")
        session_token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        session = AuthenticatedSession(
            session_id=1,
            user=self.user,
            session_token_hash=hash_session_secret(session_token),
            csrf_token_hash=hash_session_secret(csrf_token),
            expires_at=datetime.now(UTC) + SESSION_LIFETIME,
            csrf_token=csrf_token,
        )
        self.sessions[session.session_token_hash] = session
        return AuthResult(self.user, session_token, csrf_token)

    def get_session(self, session_token: str | None, *, rotate_csrf: bool = False):
        if not session_token:
            return None
        session = self.sessions.get(hash_session_secret(session_token))
        if session is None or session.expires_at <= datetime.now(UTC):
            return None
        if not rotate_csrf:
            return session
        csrf_token = secrets.token_urlsafe(32)
        session = replace(
            session,
            csrf_token_hash=hash_session_secret(csrf_token),
            csrf_token=csrf_token,
        )
        self.sessions[session.session_token_hash] = session
        return session

    def revoke_session(self, session: AuthenticatedSession) -> None:
        self.sessions.pop(session.session_token_hash, None)

    def complete_demo(self, user_id: int) -> bool:
        return user_id == self.user.user_id


class SmokePlatformRepository:
    def __init__(self):
        self.plans: dict[int, PlanRecord] = {}
        self.owner_ids: dict[int, int] = {}
        self.next_plan_id = 1

    def list_crops(self):
        return [
            {
                "crop_id": "tomato",
                "canonical_name_en": "Tomato",
                "canonical_name_tl": "Kamatis",
                "scientific_name": "Solanum lycopersicum",
                "category": "vegetable",
            },
            {
                "crop_id": "eggplant",
                "canonical_name_en": "Eggplant",
                "canonical_name_tl": "Talong",
                "scientific_name": "Solanum melongena",
                "category": "vegetable",
            },
        ]

    def list_geographies(self):
        return [
            {
                "geography_id": "region_iii",
                "name": "Central Luzon",
                "level": "region",
                "parent_geography_id": None,
            },
            {
                "geography_id": "province_ne",
                "name": "Nueva Ecija",
                "level": "province",
                "parent_geography_id": "region_iii",
            },
            {
                "geography_id": "mun_0304903000",
                "name": "Cabanatuan City",
                "level": "municipality_city",
                "parent_geography_id": "province_ne",
            },
        ]

    def is_active_crop(self, crop_id: str) -> bool:
        return crop_id in {"tomato", "eggplant"}

    def is_supported_geography(self, geography_id: str) -> bool:
        return geography_id == "mun_0304903000"

    def list_plans(self, user_id: int) -> list[PlanRecord]:
        return [
            plan for plan_id, plan in self.plans.items()
            if self.owner_ids[plan_id] == user_id
        ]

    def get_plan(self, user_id: int, plan_id: int) -> PlanRecord | None:
        if self.owner_ids.get(plan_id) != user_id:
            return None
        return self.plans.get(plan_id)

    def create_plan(self, *, user_id: int, role: str, **values) -> PlanRecord:
        del role
        plan_id = self.next_plan_id
        self.next_plan_id += 1
        plan = PlanRecord(
            plan_id=plan_id,
            crop_id=values["crop_id"],
            crop_name_en="Tomato" if values["crop_id"] == "tomato" else "Eggplant",
            crop_name_tl="Kamatis" if values["crop_id"] == "tomato" else "Talong",
            geography_id=values["geography_id"],
            geography_name="Cabanatuan City, Nueva Ecija, Central Luzon",
            area_ha=values["area_ha"],
            planting_date=values["planting_date"],
            harvest_start=values["harvest_start"],
            harvest_end=values["harvest_end"],
            status="active",
        )
        self.owner_ids[plan_id] = user_id
        self.plans[plan_id] = plan
        return plan

    def cancel_plan(self, user_id: int, plan_id: int) -> PlanRecord | None:
        current = self.get_plan(user_id, plan_id)
        if current is None:
            return None
        cancelled = replace(current, status="cancelled")
        self.plans[plan_id] = cancelled
        return cancelled


class SmokeRiskRepository:
    def __init__(self, platform: SmokePlatformRepository):
        self.platform = platform
        self.dataset_version = load_engine_config().dataset_version

    def dataset_is_ready(self, dataset_version: str) -> bool:
        return dataset_version == self.dataset_version

    def get_crop(self, crop_id: str):
        names = {"tomato": "Tomato", "eggplant": "Eggplant"}
        name = names.get(crop_id)
        return CropRecord(crop_id, name) if name else None

    def get_geography(self, geography_id: str):
        if geography_id != "mun_0304903000":
            return None
        return GeographyRecord(geography_id, 1, "Cabanatuan City")

    def get_plans(
        self,
        crop_id: str,
        geography_id: str,
        geography_database_id: int,
        period_start: date,
        period_end: date,
    ):
        del geography_database_id
        return [
            EnginePlanRecord(
                crop_id=plan.crop_id,
                geography_id=plan.geography_id,
                area_ha=plan.area_ha,
                harvest_start=plan.harvest_start,
                harvest_end=plan.harvest_end,
                status=plan.status,
            )
            for plan in self.platform.plans.values()
            if plan.crop_id == crop_id
            and plan.geography_id == geography_id
            and plan.status == "active"
            and plan.harvest_start <= period_end
            and plan.harvest_end >= period_start
        ]

    def get_reference(
        self,
        crop_id: str,
        geography_database_id: int,
        period_start: date,
        period_end: date,
        dataset_version: str,
    ):
        del crop_id, geography_database_id, period_start, period_end
        return ReferenceRecord(Decimal("25"), "future_planning", dataset_version)


async def run_smoke() -> None:
    auth_store = SmokeAuthStore()
    platform = SmokePlatformRepository()
    risk_service = RiskService(SmokeRiskRepository(platform), load_engine_config())

    original_auth_builder = api_module.build_auth_store
    original_risk_builder = api_module.build_risk_service
    original_platform_factory = api_module.app.state.platform_repository_factory
    api_module.build_auth_store = lambda: auth_store
    api_module.build_risk_service = lambda: risk_service
    api_module.app.state.platform_repository_factory = lambda: platform
    try:
        transport = httpx.ASGITransport(app=api_module.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://127.0.0.1:3001",
        ) as client:
            login = await client.post(
                "/auth/login",
                json={
                    "email": "farmer.demo@tanim.local",
                    "password": "phase5-smoke-password",
                },
            )
            assert login.status_code == 200, login.text
            assert client.cookies.get("tanim_session")
            csrf_token = login.json()["csrf_token"]

            risk_preview = await client.post(
                "/risk/check",
                json={
                    "crop_id": "tomato",
                    "geography_id": "mun_0304903000",
                    "proposed_area_ha": 8,
                    "harvest_start": "2027-01-01",
                    "harvest_end": "2027-03-31",
                    "comparison_crop_ids": ["eggplant"],
                },
            )
            assert risk_preview.status_code == 200, risk_preview.text
            assert risk_preview.json()["status"] == "available"
            assert len(risk_preview.json()["comparisons"]) == 1
            assert (await client.get("/plans")).json() == []

            saved = await client.post(
                "/plans",
                json={
                    "crop_id": "tomato",
                    "geography_id": "mun_0304903000",
                    "area_ha": 8,
                    "planting_date": "2026-10-01",
                    "harvest_start": "2027-01-01",
                    "harvest_end": "2027-03-31",
                },
                headers={"X-CSRF-Token": csrf_token},
            )
            assert saved.status_code == 201, saved.text
            plan_id = saved.json()["plan_id"]

            plans = await client.get("/plans")
            assert plans.status_code == 200, plans.text
            assert len(plans.json()) == 1
            assert plans.json()[0]["plan_id"] == plan_id

            cancelled = await client.delete(
                f"/plans/{plan_id}",
                headers={"X-CSRF-Token": csrf_token},
            )
            assert cancelled.status_code == 200, cancelled.text
            assert cancelled.json()["status"] == "cancelled"
            after_cancel = await client.get("/plans")
            assert after_cancel.status_code == 200, after_cancel.text
    finally:
        api_module.build_auth_store = original_auth_builder
        api_module.build_risk_service = original_risk_builder
        api_module.app.state.platform_repository_factory = original_platform_factory


def main() -> int:
    asyncio.run(run_smoke())
    print(
        "Platform smoke passed: login, risk preview, plan save, list, and cancel are working."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
