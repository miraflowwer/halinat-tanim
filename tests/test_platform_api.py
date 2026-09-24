import asyncio
import secrets
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
from services.api.config import PRIVACY_NOTICE_VERSION, SESSION_LIFETIME
from services.api.platform_repository import (
    CooperativePlanRecord,
    OrganizationRecord,
    PlanRecord,
)
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


class MemoryAuthStore:
    def __init__(self):
        self.next_user_id = 1
        self.sessions: dict[str, AuthenticatedSession] = {}

    def register(self, **values) -> AuthResult:
        user = AuthUser(
            user_id=self.next_user_id,
            display_name=values["display_name"],
            email=values["email"].lower(),
            role=values["role"],
            preferred_language=values.get("preferred_language", "en"),
            has_completed_demo=False,
        )
        self.next_user_id += 1
        return self._issue(user)

    def _issue(self, user: AuthUser) -> AuthResult:
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        session = AuthenticatedSession(
            session_id=len(self.sessions) + 1,
            user=user,
            session_token_hash=hash_session_secret(token),
            csrf_token_hash=hash_session_secret(csrf),
            expires_at=datetime.now(UTC) + SESSION_LIFETIME,
        )
        self.sessions[session.session_token_hash] = session
        return AuthResult(user, token, csrf)

    def get_session(self, token: str | None, *, rotate_csrf: bool = False):
        if not token:
            return None
        session_hash = hash_session_secret(token)
        session = self.sessions.get(session_hash)
        if not session or session.expires_at <= datetime.now(UTC):
            return None
        if rotate_csrf:
            csrf = secrets.token_urlsafe(32)
            session = AuthenticatedSession(
                session.session_id,
                session.user,
                session.session_token_hash,
                hash_session_secret(csrf),
                session.expires_at,
                csrf,
            )
            self.sessions[session_hash] = session
        return session

    def revoke_session(self, session: AuthenticatedSession) -> None:
        self.sessions.pop(session.session_token_hash, None)

    def complete_demo(self, user_id: int) -> bool:
        return True


class MemoryPlatformRepository:
    def __init__(self):
        self.crops = {
            "tomato": ("Tomato", "Kamatis"),
            "eggplant": ("Eggplant", "Talong"),
        }
        self.geographies = {
            "region_iii": ("Central Luzon", "region", None),
            "province_ne": ("Nueva Ecija", "province", "region_iii"),
            "mun_cabanatuan": ("Cabanatuan City", "municipality_city", "province_ne"),
        }
        self.organizations = {
            1: (101, "Cooperative One"),
            2: (202, "Cooperative Two"),
        }
        self.plans: dict[int, PlanRecord] = {}
        self.plan_owners: dict[int, int] = {}
        self.plan_organizations: dict[int, int | None] = {}
        self.next_plan_id = 1

    def list_crops(self):
        return [
            {
                "crop_id": crop_id,
                "canonical_name_en": names[0],
                "canonical_name_tl": names[1],
                "scientific_name": None,
                "category": "vegetable",
            }
            for crop_id, names in self.crops.items()
        ]

    def list_geographies(self):
        return [
            {
                "geography_id": geography_id,
                "name": value[0],
                "level": value[1],
                "parent_geography_id": value[2],
            }
            for geography_id, value in self.geographies.items()
        ]

    def is_active_crop(self, crop_id: str) -> bool:
        return crop_id in self.crops

    def is_supported_geography(self, geography_id: str) -> bool:
        value = self.geographies.get(geography_id)
        return value is not None and value[1] == "municipality_city"

    def _make_plan(
        self,
        plan_id: int,
        crop_id: str,
        geography_id: str,
        area_ha: Decimal,
        planting_date: date,
        harvest_start: date,
        harvest_end: date,
        status: str,
    ) -> PlanRecord:
        geography_name = self.geographies[geography_id][0]
        crop_name = self.crops[crop_id]
        return PlanRecord(
            plan_id,
            crop_id,
            crop_name[0],
            crop_name[1],
            geography_id,
            geography_name,
            Decimal(area_ha),
            planting_date,
            harvest_start,
            harvest_end,
            status,
        )

    def list_plans(self, user_id: int):
        return [
            plan
            for plan_id, plan in self.plans.items()
            if self.plan_owners[plan_id] == user_id
        ]

    def get_plan(self, user_id: int, plan_id: int):
        if self.plan_owners.get(plan_id) != user_id:
            return None
        return self.plans[plan_id]

    def create_plan(self, *, user_id: int, role: str, **values):
        plan_id = self.next_plan_id
        self.next_plan_id += 1
        self.plan_owners[plan_id] = user_id
        self.plan_organizations[plan_id] = (
            self.organizations[user_id][0] if role == "cooperative" else None
        )
        plan = self._make_plan(plan_id, status="active", **values)
        self.plans[plan_id] = plan
        return plan

    def update_plan(self, *, user_id: int, plan_id: int, **values):
        current = self.get_plan(user_id, plan_id)
        if current is None or current.status != "active":
            return None
        updated = self._make_plan(plan_id, status="active", **values)
        self.plans[plan_id] = updated
        return updated

    def cancel_plan(self, user_id: int, plan_id: int):
        current = self.get_plan(user_id, plan_id)
        if current is None:
            return None
        cancelled = PlanRecord(
            **{
                **current.__dict__,
                "status": "cancelled",
            }
        )
        self.plans[plan_id] = cancelled
        return cancelled

    def cooperative_plans(self, user_id: int):
        membership = self.organizations.get(user_id)
        if membership is None:
            return None
        organization_id, name = membership
        plans = []
        for plan_id, plan in self.plans.items():
            if self.plan_organizations[plan_id] != organization_id or plan.status != "active":
                continue
            plans.append(
                CooperativePlanRecord(
                    plan.crop_id,
                    plan.crop_name_en,
                    plan.crop_name_tl,
                    plan.geography_id,
                    plan.geography_name,
                    plan.area_ha,
                    plan.harvest_start,
                    plan.harvest_end,
                )
            )
        return OrganizationRecord(organization_id, name), plans

    def has_organization_membership(self, user_id: int) -> bool:
        return user_id in self.organizations


class MemoryRiskRepository:
    def __init__(self, platform: MemoryPlatformRepository):
        self.platform = platform

    def dataset_is_ready(self, dataset_version: str) -> bool:
        return dataset_version == load_engine_config().dataset_version

    def get_crop(self, crop_id: str):
        if crop_id not in self.platform.crops:
            return None
        return CropRecord(crop_id, self.platform.crops[crop_id][0])

    def get_geography(self, geography_id: str):
        if not self.platform.is_supported_geography(geography_id):
            return None
        return GeographyRecord(geography_id, 1, self.platform.geographies[geography_id][0])

    def get_plans(
        self,
        crop_id: str,
        geography_id: str,
        geography_database_id: int,
        period_start: date,
        period_end: date,
    ):
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
        return ReferenceRecord(Decimal("25"), "future_planning", dataset_version)


def client_for(monkeypatch, auth_store, platform_repository):
    monkeypatch.setattr(api_module, "build_auth_store", lambda: auth_store)
    monkeypatch.setattr(
        api_module.app.state,
        "platform_repository_factory",
        lambda: platform_repository,
    )
    monkeypatch.setattr(
        api_module,
        "build_risk_service",
        lambda: RiskService(MemoryRiskRepository(platform_repository), load_engine_config()),
    )

    async def create_client():
        transport = httpx.ASGITransport(app=api_module.app)
        client = httpx.AsyncClient(transport=transport, base_url="http://test")
        return client

    return asyncio.run(create_client())


def registration_payload(email: str, role: str = "farmer"):
    return {
        "display_name": "Tanim User",
        "email": email,
        "password": "safe-password",
        "role": role,
        "privacy_notice_version": PRIVACY_NOTICE_VERSION,
        "privacy_accepted": True,
        "optional_data_improvement_consent": False,
        "organization_name": "Test Cooperative" if role == "cooperative" else None,
    }


def plan_payload(**overrides):
    return {
        "crop_id": "tomato",
        "geography_id": "mun_cabanatuan",
        "area_ha": 8,
        "planting_date": "2026-10-01",
        "harvest_start": "2027-01-01",
        "harvest_end": "2027-03-31",
        **overrides,
    }


def test_plan_crud_ownership_validation_and_cancel_excludes_engine_area(monkeypatch):
    auth_store = MemoryAuthStore()
    platform = MemoryPlatformRepository()
    client = client_for(monkeypatch, auth_store, platform)

    async def flow():
        unauthenticated = await client.get("/plans")
        registration = await client.post(
            "/auth/register",
            json=registration_payload("one@test.invalid"),
        )
        csrf = registration.json()["csrf_token"]
        assert (await client.get("/plans")).json() == []

        preview = await client.post(
            "/risk/check",
            json={
                "crop_id": "tomato",
                "geography_id": "mun_cabanatuan",
                "proposed_area_ha": 8,
                "harvest_start": "2027-01-01",
                "harvest_end": "2027-03-31",
            },
        )
        empty_after_preview = await client.get("/plans")
        missing_csrf = await client.post("/plans", json=plan_payload())
        invalid_csrf = await client.post(
            "/plans",
            json=plan_payload(),
            headers={"X-CSRF-Token": "not-a-valid-token"},
        )
        bad_crop = await client.post(
            "/plans",
            json=plan_payload(crop_id="unknown"),
            headers={"X-CSRF-Token": csrf},
        )
        bad_geography = await client.post(
            "/plans",
            json=plan_payload(geography_id="region_iii"),
            headers={"X-CSRF-Token": csrf},
        )
        bad_area = await client.post(
            "/plans",
            json=plan_payload(area_ha=0),
            headers={"X-CSRF-Token": csrf},
        )
        bad_negative_area = await client.post(
            "/plans",
            json=plan_payload(area_ha=-1),
            headers={"X-CSRF-Token": csrf},
        )
        bad_date = await client.post(
            "/plans",
            json=plan_payload(harvest_start="2027-02-30"),
            headers={"X-CSRF-Token": csrf},
        )
        bad_harvest = await client.post(
            "/plans",
            json=plan_payload(harvest_start="2027-03-20", harvest_end="2027-04-10"),
            headers={"X-CSRF-Token": csrf},
        )
        unsupported_harvest = await client.post(
            "/plans",
            json=plan_payload(harvest_start="2029-01-01", harvest_end="2029-03-31"),
            headers={"X-CSRF-Token": csrf},
        )
        malformed_plan_id = await client.get("/plans/not-a-number")
        created = await client.post(
            "/plans",
            json=plan_payload(),
            headers={"X-CSRF-Token": csrf},
        )
        listed = await client.get("/plans")
        details = await client.get("/plans/1")

        second = await client.post("/auth/register", json=registration_payload("two@test.invalid"))
        second_csrf = second.json()["csrf_token"]
        hidden = await client.get("/plans/1")
        denied_edit = await client.patch(
            "/plans/1",
            json={"area_ha": 11},
            headers={"X-CSRF-Token": second_csrf},
        )

        client.cookies.set("tanim_session", registration.cookies["tanim_session"])
        changed = await client.patch(
            "/plans/1",
            json={"area_ha": 20},
            headers={"X-CSRF-Token": csrf},
        )
        higher_risk = await client.post(
            "/risk/check",
            json={
                "crop_id": "tomato",
                "geography_id": "mun_cabanatuan",
                "proposed_area_ha": 8,
                "harvest_start": "2027-01-01",
                "harvest_end": "2027-03-31",
            },
        )
        cancelled = await client.delete("/plans/1", headers={"X-CSRF-Token": csrf})
        after_cancel = await client.post(
            "/risk/check",
            json={
                "crop_id": "tomato",
                "geography_id": "mun_cabanatuan",
                "proposed_area_ha": 8,
                "harvest_start": "2027-01-01",
                "harvest_end": "2027-03-31",
            },
        )
        return locals()

    try:
        result = asyncio.run(flow())
    finally:
        asyncio.run(client.aclose())

    assert result["unauthenticated"].status_code == 401
    assert result["preview"].status_code == 200
    assert result["preview"].json()["risk"] == "low"
    assert result["empty_after_preview"].json() == []
    assert result["missing_csrf"].status_code == 403
    assert result["invalid_csrf"].status_code == 403
    assert result["bad_crop"].json()["detail"]["code"] == "UNSUPPORTED_CROP"
    assert result["bad_geography"].json()["detail"]["code"] == "UNSUPPORTED_GEOGRAPHY"
    assert result["bad_area"].json()["detail"]["code"] == "INVALID_AREA"
    assert result["bad_negative_area"].json()["detail"]["code"] == "INVALID_AREA"
    assert result["bad_date"].json()["detail"]["code"] == "INVALID_DATE"
    assert result["bad_harvest"].json()["detail"]["code"] == "HARVEST_PERIOD_SPANS_MULTIPLE_PERIODS"
    assert result["unsupported_harvest"].json()["detail"]["code"] == "UNSUPPORTED_HARVEST_PERIOD"
    assert result["malformed_plan_id"].json()["detail"]["code"] == "INVALID_REQUEST"
    assert result["created"].status_code == 201
    assert result["listed"].json()[0]["plan_id"] == 1
    assert result["details"].json()["status"] == "active"
    assert result["hidden"].status_code == 404
    assert result["denied_edit"].status_code == 404
    assert result["changed"].json()["area_ha"] == 20
    assert result["higher_risk"].json()["risk"] == "high"
    assert result["cancelled"].json()["status"] == "cancelled"
    assert result["after_cancel"].json()["risk"] == "low"
    assert len(platform.plans) == 1


def test_cooperative_overview_is_role_and_organization_scoped(monkeypatch):
    auth_store = MemoryAuthStore()
    platform = MemoryPlatformRepository()
    client = client_for(monkeypatch, auth_store, platform)

    async def flow():
        first = await client.post(
            "/auth/register",
            json=registration_payload("coop-one@test.invalid", "cooperative"),
        )
        first_csrf = first.json()["csrf_token"]
        await client.post(
            "/plans",
            json=plan_payload(area_ha=5),
            headers={"X-CSRF-Token": first_csrf},
        )
        first_overview = await client.get("/cooperative/overview")

        second = await client.post(
            "/auth/register",
            json=registration_payload("coop-two@test.invalid", "cooperative"),
        )
        second_csrf = second.json()["csrf_token"]
        await client.post(
            "/plans",
            json=plan_payload(area_ha=25),
            headers={"X-CSRF-Token": second_csrf},
        )
        second_overview = await client.get("/cooperative/overview")

        await client.post(
            "/auth/register",
            json=registration_payload("farmer@test.invalid"),
        )
        farmer_overview = await client.get("/cooperative/overview")
        return first_overview, second_overview, farmer_overview

    try:
        first, second, farmer = asyncio.run(flow())
    finally:
        asyncio.run(client.aclose())

    assert first.status_code == 200
    assert first.json()["total_active_plan_count"] == 1
    assert first.json()["aggregates"][0]["planned_area_ha"] == 5
    assert second.status_code == 200
    assert second.json()["aggregates"][0]["planned_area_ha"] == 25
    assert second.json()["aggregates"][0]["community_risk"]["risk"] == "high"
    assert "email" not in first.text
    assert "display_name" not in first.text
    assert "user_id" not in first.text
    assert farmer.status_code == 403
