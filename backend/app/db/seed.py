"""
Creates one admin user (role='admin') for local dev / initial access.

Credentials come from env vars, with dev-safe defaults so this runs
out of the box in a fresh docker-compose environment:

    ADMIN_EMAIL     default: admin@sanestix.com
    ADMIN_PASSWORD  default: ChangeMe123!

Override them (recommended) by exporting the env vars before running,
or by setting them in docker-compose.yml / .env. Safe to re-run — it
skips creation if a user with that email already exists.

Run inside the backend container:
    docker compose -f docker/docker-compose.yml exec backend python -m app.db.seed
"""

import os

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@sanestix.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")


def seed_admin_user() -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existing is not None:
            print(f"Admin user already exists: {ADMIN_EMAIL} (id={existing.id}) — skipping.")
            return

        admin = User(
            name="Admin",
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            role="admin",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"Created admin user: {admin.email} (id={admin.id}, role={admin.role})")
        print(f"Login with: email={ADMIN_EMAIL}  password={ADMIN_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin_user()
