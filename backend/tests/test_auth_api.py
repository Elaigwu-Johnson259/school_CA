"""
End-to-end tests for the /api/auth/* endpoints, using the `client` +
`db_session` fixtures from conftest.py (in-memory SQLite, real HTTP calls
through FastAPI's TestClient).
"""
from datetime import datetime, timedelta, timezone

from jose import jwt
import pytest

from app.core.config import settings
from app.core.security import hash_password
from app.models.school import School
from app.models.user import User
from app.models.enums import UserRole


def _make_school(db_session, name="Greenfield High"):
    school = School(name=name, email=f"{name.lower().replace(' ', '')}@example.com")
    db_session.add(school)
    db_session.commit()
    db_session.refresh(school)
    return school


def _make_user(db_session, *, email, password, role, school=None, is_active=True):
    user = User(
        school_id=school.id if school else None,
        email=email,
        hashed_password=hash_password(password),
        role=role,
        is_active=is_active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_login_succeeds_with_valid_credentials(client, db_session):
    school = _make_school(db_session)
    _make_user(
        db_session, email="admin@example.com", password="s3cret-pass", role=UserRole.SCHOOL_ADMIN,
        school=school,
    )

    response = client.post(
        "/api/auth/login", json={"email": "admin@example.com", "password": "s3cret-pass"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "admin@example.com"
    assert body["user"]["role"] == "SCHOOL_ADMIN"
    # the hashed password must never be present in an API response
    assert "hashed_password" not in body["user"]
    assert "password" not in body["user"]


def test_login_fails_with_wrong_password(client, db_session):
    _make_user(db_session, email="admin@example.com", password="s3cret-pass", role=UserRole.SCHOOL_ADMIN)

    response = client.post(
        "/api/auth/login", json={"email": "admin@example.com", "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_fails_for_unknown_email_with_same_message_as_wrong_password(client, db_session):
    """Same status + message as a wrong password, to avoid account enumeration."""
    response = client.post(
        "/api/auth/login", json={"email": "nobody@example.com", "password": "whatever"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_inactive_user_cannot_login(client, db_session):
    _make_user(
        db_session, email="exteacher@example.com", password="s3cret-pass",
        role=UserRole.TEACHER, is_active=False,
    )

    response = client.post(
        "/api/auth/login", json={"email": "exteacher@example.com", "password": "s3cret-pass"}
    )

    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_access_token_authenticates_me_endpoint(client, db_session):
    school = _make_school(db_session)
    user = _make_user(
        db_session, email="teacher@example.com", password="s3cret-pass",
        role=UserRole.TEACHER, school=school,
    )

    login_response = client.post(
        "/api/auth/login", json={"email": "teacher@example.com", "password": "s3cret-pass"}
    )
    access_token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert me_response.status_code == 200
    body = me_response.json()
    assert body["id"] == user.id
    assert body["email"] == "teacher@example.com"
    assert body["role"] == "TEACHER"
    assert body["school_id"] == school.id
    assert body["is_active"] is True


def test_invalid_token_is_rejected(client):
    response = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


def test_expired_token_is_rejected(client, db_session):
    user = _make_user(
        db_session, email="teacher@example.com", password="s3cret-pass", role=UserRole.TEACHER
    )
    expired_payload = {
        "sub": str(user.id),
        "type": "access",
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    expired_token = jwt.encode(
        expired_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )

    response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401


def test_refresh_token_issues_new_access_token(client, db_session):
    _make_user(db_session, email="admin@example.com", password="s3cret-pass", role=UserRole.SCHOOL_ADMIN)

    login_response = client.post(
        "/api/auth/login", json={"email": "admin@example.com", "password": "s3cret-pass"}
    )
    refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 200
    new_access_token = refresh_response.json()["access_token"]

    # the newly issued access token should itself work against /me
    me_response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert me_response.status_code == 200


def test_access_token_cannot_be_used_as_refresh_token(client, db_session):
    _make_user(db_session, email="admin@example.com", password="s3cret-pass", role=UserRole.SCHOOL_ADMIN)

    login_response = client.post(
        "/api/auth/login", json={"email": "admin@example.com", "password": "s3cret-pass"}
    )
    access_token = login_response.json()["access_token"]

    response = client.post("/api/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401


def test_logout_revokes_the_refresh_token(client, db_session):
    _make_user(db_session, email="admin@example.com", password="s3cret-pass", role=UserRole.SCHOOL_ADMIN)

    login_response = client.post(
        "/api/auth/login", json={"email": "admin@example.com", "password": "s3cret-pass"}
    )
    refresh_token = login_response.json()["refresh_token"]

    logout_response = client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    assert logout_response.status_code == 204

    # the same refresh token must no longer work
    refresh_response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 401
