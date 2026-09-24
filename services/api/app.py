import logging
import math
import os
from datetime import date
from decimal import Decimal
from typing import Literal

import psycopg
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from services.api.auth import (
    AuthenticatedSession,
    AuthError,
    AuthResult,
    AuthStore,
    normalize_email,
    verify_csrf_token,
)
from services.api.config import (
    SESSION_COOKIE_NAME,
    SESSION_LIFETIME_SECONDS,
    allowed_origins,
    session_cookie_secure,
)
from services.api.demo import (
    DemoNotReadyError,
    DemoScenarioRecord,
    DemoScenarioResult,
    DemoService,
    PostgresDemoRepository,
)
from services.api.platform_repository import PostgresPlatformRepository
from services.api.routes.cooperative import router as cooperative_router
from services.api.routes.lookups import router as lookups_router
from services.api.routes.plans import router as plans_router
from services.engine.config import load_engine_config
from services.engine.models import RiskCheckInput, RiskCheckResult
from services.engine.periods import EngineInputError
from services.engine.repository import (
    DatasetNotReadyError,
    PostgresRiskRepository,
    RepositoryError,
)
from services.engine.service import RiskService

logger = logging.getLogger(__name__)
app = FastAPI(title="TANIM API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)


def _decimal_as_json_number(value: Decimal | None) -> float | str | None:
    if value is None:
        return None
    numeric = float(value)
    if math.isfinite(numeric):
        return numeric
    return format(value, "f")


class RiskCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crop_id: str = Field(min_length=1)
    geography_id: str = Field(min_length=1)
    proposed_area_ha: Decimal
    harvest_start: str = Field(min_length=1)
    harvest_end: str = Field(min_length=1)
    comparison_crop_ids: list[str] = Field(default_factory=list)

    @field_validator("crop_id", "geography_id", "harvest_start", "harvest_end")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be blank")
        return cleaned

    @field_validator("proposed_area_ha")
    @classmethod
    def area_must_be_positive_and_finite(cls, value: Decimal) -> Decimal:
        if not value.is_finite() or value <= 0:
            raise ValueError("proposed_area_ha must be a finite number greater than zero")
        return value

    @field_validator("comparison_crop_ids")
    @classmethod
    def comparison_ids_must_not_be_blank(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("comparison crop IDs must not be blank")
        return cleaned


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=160)
    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=256)
    role: Literal["farmer", "cooperative"]
    privacy_notice_version: str = Field(min_length=1, max_length=80)
    privacy_accepted: bool
    optional_data_improvement_consent: bool = False
    preferred_language: Literal["en", "tl"] = "en"
    organization_name: str | None = Field(default=None, max_length=200)

    @field_validator("display_name", "email", "privacy_notice_version")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be blank")
        return cleaned

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, value: str) -> str:
        try:
            return normalize_email(value)
        except ValueError:
            raise ValueError("email must be valid") from None

    @field_validator("organization_name")
    @classmethod
    def optional_text_must_be_cleaned(cls, value: str | None) -> str | None:
        return value.strip() if value and value.strip() else None


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class UserResponse(BaseModel):
    user_id: int
    display_name: str
    email: str
    role: Literal["farmer", "cooperative"]
    preferred_language: Literal["en", "tl"]
    has_completed_demo: bool


class AuthenticatedResponse(BaseModel):
    authenticated: bool
    user: UserResponse
    csrf_token: str


class DemoScenarioResponse(BaseModel):
    scenario_id: str
    crop_id: str
    crop_name_en: str
    crop_name_tl: str | None
    geography_id: str
    geography_name: str
    period_start: date
    period_end: date
    existing_planned_area_ha: Decimal
    proposed_area_ha: Decimal
    projected_area_ha: Decimal
    reference_area_ha: Decimal
    ratio: Decimal
    risk: Literal["low", "moderate", "high"]
    explanation: str | None = None

    @field_serializer(
        "existing_planned_area_ha",
        "proposed_area_ha",
        "projected_area_ha",
        "reference_area_ha",
        "ratio",
        when_used="json",
    )
    def decimal_as_number(self, value: Decimal) -> float | str:
        return _decimal_as_json_number(value)  # type: ignore[return-value]


class DemoComparisonResponse(BaseModel):
    scenario_id: str
    crop_id: str
    crop_name_en: str
    crop_name_tl: str | None
    geography_id: str
    geography_name: str
    period_start: date
    period_end: date
    existing_planned_area_ha: Decimal
    proposed_area_ha: Decimal
    reference_area_ha: Decimal
    current_ratio: Decimal
    current_risk: Literal["low", "moderate", "high"]
    projected_ratio_if_same_area: Decimal
    projected_risk_if_same_area: Literal["low", "moderate", "high"]

    @field_serializer(
        "existing_planned_area_ha",
        "proposed_area_ha",
        "reference_area_ha",
        "current_ratio",
        "projected_ratio_if_same_area",
        when_used="json",
    )
    def decimal_as_number(self, value: Decimal) -> float | str:
        return _decimal_as_json_number(value)  # type: ignore[return-value]


class DemoResponse(BaseModel):
    dataset_version: str
    data_kind: Literal["synthetic_demo"]
    primary: DemoScenarioResponse
    comparison: DemoComparisonResponse


class ComparisonResponse(BaseModel):
    crop_id: str
    existing_planned_area_ha: Decimal
    reference_area_ha: Decimal | None
    current_ratio: Decimal | None
    current_risk: Literal["low", "moderate", "high"] | None
    projected_ratio_if_same_area: Decimal | None
    projected_risk_if_same_area: Literal["low", "moderate", "high"] | None

    @field_serializer(
        "existing_planned_area_ha",
        "reference_area_ha",
        "current_ratio",
        "projected_ratio_if_same_area",
        when_used="json",
    )
    def decimal_as_number(self, value: Decimal | None) -> float | str | None:
        return _decimal_as_json_number(value)


class RiskCheckResponse(BaseModel):
    status: Literal["available", "unavailable"]
    crop_id: str
    geography_id: str
    requested_harvest_start: date
    requested_harvest_end: date
    planning_period_start: date
    planning_period_end: date
    existing_planned_area_ha: Decimal
    proposed_area_ha: Decimal
    projected_planned_area_ha: Decimal
    reference_area_ha: Decimal | None
    ratio: Decimal | None
    risk: Literal["low", "moderate", "high"] | None
    contributing_plan_count: int
    assumption_version: str
    dataset_version: str
    explanation: str
    comparisons: list[ComparisonResponse]

    @field_serializer(
        "existing_planned_area_ha",
        "proposed_area_ha",
        "projected_planned_area_ha",
        "reference_area_ha",
        "ratio",
        when_used="json",
    )
    def decimal_as_number(self, value: Decimal | None) -> float | str | None:
        return _decimal_as_json_number(value)


def build_risk_service() -> RiskService:
    return RiskService(
        PostgresRiskRepository.from_environment(),
        load_engine_config(),
    )


def build_auth_store() -> AuthStore:
    return AuthStore.from_environment()


def build_demo_service() -> DemoService:
    return DemoService(
        PostgresDemoRepository.from_environment(),
        load_engine_config(),
    )


def _user_response(user) -> dict[str, object]:
    return UserResponse(
        user_id=user.user_id,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        preferred_language=user.preferred_language,
        has_completed_demo=user.has_completed_demo,
    ).model_dump(mode="json")


def _authenticated_response(result: AuthResult) -> JSONResponse:
    body = AuthenticatedResponse(
        authenticated=True,
        user=_user_response_model(result.user),
        csrf_token=result.csrf_token,
    ).model_dump(mode="json")
    response = JSONResponse(content=body)
    _set_session_cookie(response, result.session_token)
    return response


def _user_response_model(user) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        preferred_language=user.preferred_language,
        has_completed_demo=user.has_completed_demo,
    )


def _set_session_cookie(response: Response, session_token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=SESSION_LIFETIME_SECONDS,
        httponly=True,
        secure=session_cookie_secure(),
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        secure=session_cookie_secure(),
        samesite="lax",
    )


def _raise_auth_error(error: AuthError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    ) from None


def _authenticated_session(request: Request, store: AuthStore) -> AuthenticatedSession:
    try:
        session = store.get_session(request.cookies.get(SESSION_COOKIE_NAME))
    except AuthError as error:
        _raise_auth_error(error)
    if session is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHENTICATED", "message": "Please sign in to continue."},
        )
    return session


def _require_csrf(request: Request, session: AuthenticatedSession) -> None:
    csrf_token = request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(session, csrf_token):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "CSRF_INVALID",
                "message": "This action could not be verified. Refresh and try again.",
            },
        )


def _demo_item(
    record: DemoScenarioRecord,
    *,
    projected_area: Decimal,
    ratio: Decimal,
    risk: str,
    explanation: str | None = None,
    proposed_area: Decimal | None = None,
) -> DemoScenarioResponse:
    return DemoScenarioResponse(
        scenario_id=record.scenario_id,
        crop_id=record.crop_id,
        crop_name_en=record.crop_name_en,
        crop_name_tl=record.crop_name_tl,
        geography_id=record.geography_id,
        geography_name=record.geography_name,
        period_start=record.period_start,
        period_end=record.period_end,
        existing_planned_area_ha=record.existing_planned_area_ha,
        proposed_area_ha=(
            record.proposed_future_plan_area_ha if proposed_area is None else proposed_area
        ),
        projected_area_ha=projected_area,
        reference_area_ha=record.reference_area_ha,
        ratio=ratio,
        risk=risk,  # type: ignore[arg-type]
        explanation=explanation,
    )


def _demo_response(result: DemoScenarioResult) -> DemoResponse:
    primary = _demo_item(
        result.primary,
        projected_area=result.projected_area_ha,
        ratio=result.ratio,
        risk=result.risk,
        explanation=result.explanation,
    )
    comparison = DemoComparisonResponse(
        scenario_id=result.comparison.scenario_id,
        crop_id=result.comparison.crop_id,
        crop_name_en=result.comparison.crop_name_en,
        crop_name_tl=result.comparison.crop_name_tl,
        geography_id=result.comparison.geography_id,
        geography_name=result.comparison.geography_name,
        period_start=result.comparison.period_start,
        period_end=result.comparison.period_end,
        existing_planned_area_ha=result.comparison.existing_planned_area_ha,
        proposed_area_ha=result.primary.proposed_future_plan_area_ha,
        reference_area_ha=result.comparison.reference_area_ha,
        current_ratio=result.comparison_current_ratio,
        current_risk=result.comparison_current_risk,  # type: ignore[arg-type]
        projected_ratio_if_same_area=result.comparison_projected_ratio,
        projected_risk_if_same_area=result.comparison_projected_risk,  # type: ignore[arg-type]
    )
    return DemoResponse(
        dataset_version=result.primary.dataset_version,
        data_kind="synthetic_demo",
        primary=primary,
        comparison=comparison,
    )


def _risk_response(result: RiskCheckResult) -> RiskCheckResponse:
    return RiskCheckResponse(
        status=result.status,
        crop_id=result.crop_id,
        geography_id=result.geography_id,
        requested_harvest_start=result.requested_harvest_start,
        requested_harvest_end=result.requested_harvest_end,
        planning_period_start=result.planning_period_start,
        planning_period_end=result.planning_period_end,
        existing_planned_area_ha=result.existing_planned_area_ha,
        proposed_area_ha=result.proposed_area_ha,
        projected_planned_area_ha=result.projected_planned_area_ha,
        reference_area_ha=result.reference_area_ha,
        ratio=result.ratio,
        risk=result.risk,
        contributing_plan_count=result.contributing_plan_count,
        assumption_version=result.assumption_version,
        dataset_version=result.dataset_version,
        explanation=result.explanation,
        comparisons=[
            ComparisonResponse(**comparison.__dict__) for comparison in result.comparisons
        ],
    )


def _validation_code(errors: list[dict[str, object]]) -> str:
    locations = {str(part) for error in errors for part in error.get("loc", ())}
    if "email" in locations:
        return "INVALID_EMAIL"
    if "password" in locations:
        return "INVALID_PASSWORD"
    if "role" in locations:
        return "INVALID_ROLE"
    if "privacy_notice_version" in locations:
        return "PRIVACY_NOTICE_VERSION_UNSUPPORTED"
    if "proposed_area_ha" in locations or "area_ha" in locations:
        return "INVALID_AREA"
    if "harvest_start" in locations or "harvest_end" in locations or "planting_date" in locations:
        return "INVALID_DATE"
    return "INVALID_REQUEST"


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(_request, exception: RequestValidationError):
    errors = exception.errors()
    code = _validation_code(errors)
    messages = {
        "INVALID_EMAIL": "Enter a valid email address.",
        "INVALID_PASSWORD": "Enter a password.",
        "INVALID_ROLE": "Choose Farmer or Cooperative.",
        "PRIVACY_NOTICE_VERSION_UNSUPPORTED": "Open the current Privacy Notice and try again.",
        "INVALID_AREA": "The area must be greater than zero.",
        "INVALID_DATE": "Use valid ISO dates.",
        "INVALID_REQUEST": "The request is not valid.",
    }
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "code": code,
                "message": messages.get(code, messages["INVALID_REQUEST"]),
            }
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the API process can serve requests."""
    return {"status": "healthy"}


@app.get("/health/db")
def database_health() -> dict[str, str]:
    """Check PostgreSQL without returning connection details to the caller."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "unavailable",
                "message": "DATABASE_URL is not configured.",
            },
        )

    try:
        with psycopg.connect(database_url, connect_timeout=3) as connection:
            connection.execute("SELECT 1")
    except (psycopg.Error, ValueError) as error:
        logger.warning("Database health check failed (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "unavailable",
                "message": "PostgreSQL is not reachable. Check DATABASE_URL and the local server.",
            },
        ) from None

    return {"status": "healthy", "database": "reachable"}


@app.post("/auth/register")
def register(request: RegisterRequest):
    try:
        result = build_auth_store().register(
            display_name=request.display_name,
            email=request.email,
            password=request.password,
            role=request.role,
            privacy_notice_version=request.privacy_notice_version,
            privacy_accepted=request.privacy_accepted,
            optional_data_improvement_consent=request.optional_data_improvement_consent,
            preferred_language=request.preferred_language,
            organization_name=request.organization_name,
        )
    except AuthError as error:
        _raise_auth_error(error)
    return _authenticated_response(result)


@app.post("/auth/login")
def login(request: LoginRequest):
    try:
        result = build_auth_store().login(email=request.email, password=request.password)
    except AuthError as error:
        _raise_auth_error(error)
    return _authenticated_response(result)


@app.get("/auth/session")
def session(request: Request):
    store = build_auth_store()
    token = request.cookies.get(SESSION_COOKIE_NAME)
    try:
        current = store.get_session(token, rotate_csrf=True)
    except AuthError as error:
        _raise_auth_error(error)
    if current is None:
        response = JSONResponse(
            content={
                "authenticated": False,
                "user": None,
                "code": "UNAUTHENTICATED",
            }
        )
        if token:
            _clear_session_cookie(response)
        return response
    response = JSONResponse(
        content=AuthenticatedResponse(
            authenticated=True,
            user=_user_response_model(current.user),
            csrf_token=current.csrf_token or "",
        ).model_dump(mode="json")
    )
    return response


@app.post("/auth/logout")
def logout(request: Request):
    store = build_auth_store()
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        session = _authenticated_session(request, store)
        _require_csrf(request, session)
        try:
            store.revoke_session(session)
        except AuthError as error:
            _raise_auth_error(error)
    response = JSONResponse(content={"authenticated": False})
    _clear_session_cookie(response)
    return response


@app.get("/demo/scenario")
def demo_scenario(request: Request):
    _authenticated_session(request, build_auth_store())
    try:
        result = build_demo_service().get_scenario()
    except DemoNotReadyError:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATASET_NOT_READY",
                "message": (
                    "The configured TANIM demo dataset is not ready. "
                    "Run the data seed step and retry."
                ),
            },
        ) from None
    except (OSError, KeyError, ValueError) as error:
        logger.warning("Demo configuration could not be loaded (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATASET_NOT_READY",
                "message": "The configured TANIM dataset is not ready.",
            },
        ) from None
    return _demo_response(result)


@app.post("/demo/complete")
def demo_complete(request: Request):
    store = build_auth_store()
    current = _authenticated_session(request, store)
    _require_csrf(request, current)
    try:
        completed = store.complete_demo(current.user.user_id)
    except AuthError as error:
        _raise_auth_error(error)
    return {"has_completed_demo": completed}


@app.post("/risk/check", response_model=RiskCheckResponse)
def risk_check(request: RiskCheckRequest) -> RiskCheckResponse:
    try:
        result = build_risk_service().check(
            RiskCheckInput(
                crop_id=request.crop_id,
                geography_id=request.geography_id,
                proposed_area_ha=request.proposed_area_ha,
                harvest_start=request.harvest_start,
                harvest_end=request.harvest_end,
                comparison_crop_ids=tuple(request.comparison_crop_ids),
            )
        )
    except EngineInputError as error:
        raise HTTPException(
            status_code=400,
            detail={"code": error.code, "message": error.message},
        ) from None
    except DatasetNotReadyError:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATASET_NOT_READY",
                "message": (
                    "The configured TANIM dataset is not seeded. "
                    "Run the data seed step and retry."
                ),
            },
        ) from None
    except RepositoryError:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATABASE_UNAVAILABLE",
                "message": (
                    "TANIM cannot read the local data service right now. "
                    "Check PostgreSQL and retry."
                ),
            },
        ) from None
    except (OSError, KeyError, ValueError) as error:
        logger.warning("Risk configuration could not be loaded (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATASET_NOT_READY",
                "message": "The configured TANIM dataset is not ready.",
            },
        ) from None
    return _risk_response(result)


app.state.auth_store_factory = lambda: build_auth_store()
app.state.platform_repository_factory = PostgresPlatformRepository.from_environment
app.state.risk_service_factory = lambda: build_risk_service()
app.include_router(lookups_router)
app.include_router(plans_router)
app.include_router(cooperative_router)
