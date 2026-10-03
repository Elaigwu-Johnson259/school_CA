"""
Tests for authenticated school-profile management:
GET /api/schools/me (already covered partly in Phase 4's tenancy tests)
and the new PATCH /api/schools/me.
"""
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.school import School
from app.models.user import User


def _make_school(db_session, name, email):
    school = School(name=name, email=email)
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


def _login(client, email, password):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_school_admin_can_get_own_school(client, db_session):
    school = _make_school(db_session, "Greenfield Academy", "gf@example.com")
    _make_user(db_session, email="admin@gf.edu", password="pass1234", role=UserRole.SCHOOL_ADMIN, school=school)
    token = _login(client, "admin@gf.edu", "pass1234")

    response = client.get("/api/schools/me", headers=_auth(token))

    assert response.status_code == 200
    assert response.json()["id"] == school.id


def test_school_admin_can_update_own_school(client, db_session):
    school = _make_school(db_session, "Greenfield Academy", "gf@example.com")
    _make_user(db_session, email="admin@gf.edu", password="pass1234", role=UserRole.SCHOOL_ADMIN, school=school)
    token = _login(client, "admin@gf.edu", "pass1234")

    response = client.patch(
        "/api/schools/me",
        headers=_auth(token),
        json={"motto": "Excellence in all things", "phone": "+1-555-0199"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["motto"] == "Excellence in all things"
    assert body["phone"] == "+1-555-0199"
    assert body["name"] == "Greenfield Academy"  # untouched fields stay as they were


def test_school_admin_update_does_not_affect_another_school(client, db_session):
    school_a = _make_school(db_session, "School A", "a@example.com")
    school_b = _make_school(db_session, "School B", "b@example.com")
    _make_user(db_session, email="admin-a@example.com", password="pass1234", role=UserRole.SCHOOL_ADMIN, school=school_a)
    token_a = _login(client, "admin-a@example.com", "pass1234")

    response = client.patch(
        "/api/schools/me", headers=_auth(token_a), json={"motto": "School A's motto"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == school_a.id

    # School B must be completely unaffected — there's no school_id in
    # the PATCH request for a School A admin to even target School B with.
    db_session.refresh(school_b)
    assert school_b.motto is None


def test_school_admin_update_cannot_change_id_or_active_flag(client, db_session):
    """
    SchoolUpdate has no `id`/`is_active` field, so extra keys in the JSON
    body are simply ignored by Pydantic rather than applied.
    """
    school = _make_school(db_session, "Greenfield Academy", "gf@example.com")
    _make_user(db_session, email="admin@gf.edu", password="pass1234", role=UserRole.SCHOOL_ADMIN, school=school)
    token = _login(client, "admin@gf.edu", "pass1234")

    response = client.patch(
        "/api/schools/me",
        headers=_auth(token),
        json={"id": 999999, "is_active": False, "motto": "Still fine"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == school.id  # unchanged
    assert body["is_active"] is True  # unchanged
    assert body["motto"] == "Still fine"


def test_teacher_cannot_update_school_profile(client, db_session):
    school = _make_school(db_session, "Greenfield Academy", "gf@example.com")
    _make_user(db_session, email="teacher@gf.edu", password="pass1234", role=UserRole.TEACHER, school=school)
    token = _login(client, "teacher@gf.edu", "pass1234")

    response = client.patch("/api/schools/me", headers=_auth(token), json={"motto": "Nope"})

    assert response.status_code == 403


def test_student_cannot_update_school_profile(client, db_session):
    school = _make_school(db_session, "Greenfield Academy", "gf@example.com")
    _make_user(db_session, email="student@gf.edu", password="pass1234", role=UserRole.STUDENT, school=school)
    token = _login(client, "student@gf.edu", "pass1234")

    response = client.patch("/api/schools/me", headers=_auth(token), json={"motto": "Nope"})

    assert response.status_code == 403


def test_unauthenticated_update_is_rejected(client, db_session):
    response = client.patch("/api/schools/me", json={"motto": "Nope"})
    assert response.status_code == 401


def test_super_admin_cannot_update_via_me(client, db_session):
    """
    SUPER_ADMIN has no home school — /api/schools/me stays explicit and
    rejects them for both GET (Phase 4) and PATCH (Phase 5), rather than
    silently doing nothing or picking an arbitrary school.
    """
    _make_user(db_session, email="super@example.com", password="pass1234", role=UserRole.SUPER_ADMIN)
    token = _login(client, "super@example.com", "pass1234")

    response = client.patch("/api/schools/me", headers=_auth(token), json={"motto": "Nope"})

    assert response.status_code == 403


def test_school_logo_upload_is_tenant_scoped_and_does_not_expose_storage_path(client, db_session, monkeypatch, tmp_path):
    from app.core.config import settings
    monkeypatch.setattr(settings, "LOCAL_STORAGE_PATH", str(tmp_path))
    school_a = _make_school(db_session, "School A", "logo-a@example.com")
    school_b = _make_school(db_session, "School B", "logo-b@example.com")
    _make_user(db_session, email="logo-admin@example.com", password="pass1234", role=UserRole.SCHOOL_ADMIN, school=school_a)
    token = _login(client, "logo-admin@example.com", "pass1234")
    png = b"\x89PNG\r\n\x1a\n" + b"test-logo"

    uploaded = client.post("/api/schools/me/logo", headers=_auth(token), files={"file": ("logo.png", png, "image/png")})
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["logo_path"] == "/api/schools/me/logo"
    assert str(tmp_path) not in uploaded.text
    assert client.get("/api/schools/me/logo", headers=_auth(token)).content == png

    db_session.refresh(school_b)
    assert school_b.logo_path is None
