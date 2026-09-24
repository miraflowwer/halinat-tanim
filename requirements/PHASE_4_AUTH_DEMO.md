# Phase 4 authentication and first-time demo

## Scope

Phase 4 adds local Farmer and Cooperative registration, login, logout, persistent sessions, privacy consent, seeded development accounts, and the first-time TANIM demo. Password reset, email verification, OTP, social login, 2FA, passkeys, and planting-plan CRUD remain out of scope.

## Registration and consent

Registration starts at the privacy screen. The required service consent must be accepted before an account is created. The optional data-improvement consent defaults to false and is stored as a separate choice.

The current privacy notice version is `privacy-2026-09-v1`. The API rejects unknown or stale versions. User creation, required consent, optional consent, a cooperative membership when supplied, and the first session are written in one transaction.

Emails are trimmed and stored in lowercase. Farmer and Cooperative are the only accepted roles.

## Passwords

The shared password service uses Argon2id through `argon2-cffi`. Password hashes are used by registration, login, and `scripts/seed_demo_accounts.py`. Plaintext passwords are not stored or returned. Passwords must have at least eight characters.

## Sessions and CSRF

`003_auth_sessions.sql` adds `auth_sessions`. PostgreSQL stores a SHA-256 hash of the random session token and a hash of a separate CSRF token. The raw session token is sent only in a host-only HttpOnly cookie named `tanim_session`.

Sessions last seven days. They use `SameSite=Lax`, path `/`, and Secure is controlled by `TANIM_SESSION_COOKIE_SECURE`. Local development uses `127.0.0.1` and plain HTTP by default. Login always creates a new session. Logout revokes only the current session and clears the cookie.

`GET /auth/session` restores the user and rotates the CSRF token. Authenticated state-changing requests send that token in `X-CSRF-Token`. Expired and revoked sessions are rejected. Cleanup is available through `scripts/cleanup_sessions.py` and is also run when new sessions are created.

## API endpoints

Authentication endpoints:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/session`

Demo endpoints:

- `GET /demo/scenario`
- `POST /demo/complete`

The demo endpoints require authentication. Demo completion also requires CSRF protection.

## Demo accounts

Run the database migrations and data seed first. Set `TANIM_DEMO_FARMER_PASSWORD` and `TANIM_DEMO_COOP_PASSWORD` in the local `.env`, then run:

```text
npm run auth:seed-demo
```

The stable development identities are `farmer.demo@tanim.local` and `coop.demo@tanim.local`. The seed is transactional and repeat-safe. It does not overwrite an existing password. It stops when an identity conflicts with another account or when a required password is missing.

## First-time demo isolation

The demo reads the canonical `data/seeds/demo_scenarios.json` data after it is loaded into the versioned database dataset. The backend calls the Phase 3 pure risk and comparison functions for the shown calculations.

The Tomato scenario shows 32 ha existing, 8 ha proposed, 40 ha projected, 25 ha reference, a 1.60 ratio, and High risk. The Eggplant comparison shows its current pressure and the actual same-area hypothetical pressure.

The demo never inserts rows into `planting_plans`. Completion only sets `users.has_completed_demo` to true. Completion is repeat-safe. `/demo?replay=1` shows the same isolated content without resetting completion.

## Frontend behavior

The auth app provides `/privacy`, `/register`, and `/login`. New registrations and accounts that have not completed the demo go to the platform `/demo` route. Completed accounts go to `/home`. The platform checks the session before showing either route.

English and Tagalog are available before login. The selected language is saved locally and is stored in `users.preferred_language` during registration.

## Non-goals and known limitations

Phase 4 does not provide password recovery, account verification, advanced cooperative administration, planting-plan CRUD, final visual design, or a full authenticated dashboard. The authenticated `/home` route is a functional placeholder until the later platform phase.
