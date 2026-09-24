"""Shared authentication dependencies for protected API routes."""

from fastapi import Depends, HTTPException, Request

from services.api.auth import AuthenticatedSession, AuthError, AuthStore, verify_csrf_token
from services.api.config import SESSION_COOKIE_NAME


def require_authenticated_session(request: Request) -> AuthenticatedSession:
    factory = getattr(request.app.state, "auth_store_factory", None)
    store = factory() if callable(factory) else AuthStore.from_environment()
    try:
        session = store.get_session(request.cookies.get(SESSION_COOKIE_NAME))
    except AuthError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={"code": error.code, "message": error.message},
        ) from None
    if session is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHENTICATED", "message": "Please sign in to continue."},
        )
    return session


def require_csrf_session(request: Request) -> AuthenticatedSession:
    session = require_authenticated_session(request)
    if not verify_csrf_token(session, request.headers.get("X-CSRF-Token")):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "CSRF_INVALID",
                "message": "This action could not be verified. Refresh and try again.",
            },
        )
    return session


AUTHENTICATED_SESSION = Depends(require_authenticated_session)
CSRF_PROTECTED_SESSION = Depends(require_csrf_session)
