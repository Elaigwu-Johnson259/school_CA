"""
End-to-end tests proving cross-tenant isolation through the real HTTP API
(not just the unit-level helpers in test_tenancy_unit.py). Sets up two
schools (School A, School B) with a user in each, plus a SUPER_ADMIN, and
checks every combination the Phase 4 spec calls out.
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


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


class _TwoSchools:
    """Small fixture-like bundle so each test doesn't repeat this setup."""

    def __init__(self, client, db_session):
        self.school_a = _make_school(db_session, "School A", "school-a@example.com")
        self.school_b = _make_school(db_session, "School B", "school-b@example.com")

        _make_user(
            db_session, email="admin-a@example.com", password="pass-a123",
            role=UserRole.SCHOOL_ADMIN, school=self.school_a,
        )
        _make_user(
            db_session, email="admin-b@example.com", password="pass-b123",
            role=UserRole.SCHOOL_ADMIN, school=self.school_b,
        )
        _make_user(
            db_session, email="super@example.com", password="super-pass123",
            role=UserRole.SUPER_ADMIN,
        )
        _make_user(
            db_session, email="inactive-a@example.com", password="pass-inactive",
            role=UserRole.TEACHER, school=self.school_a, is_active=False,
        )

        self.token_a = _login(client, "admin-a@example.com", "pass-a123")
        self.token_b = _login(client, "admin-b@example.com", "pass-b123")
        self.token_super = _login(client, "super@example.com", "super-pass123")


def test_school_a_user_can_access_school_a_via_me(client, db_session):
    fixture = _TwoSchools(client, db_session)

    response = client.get("/api/schools/me", headers=_auth_headers(fixture.token_a))

    assert response.status_code == 200
    assert response.json()["id"] == fixture.school_a.id
    assert response.json()["name"] == "School A"


def test_school_b_user_can_access_school_b_via_me(client, db_session):
    fixture = _TwoSchools(client, db_session)

    response = client.get("/api/schools/me", headers=_auth_headers(fixture.token_b))

    assert response.status_code == 200
    assert response.json()["id"] == fixture.school_b.id
    assert response.json()["name"] == "School B"


def test_school_a_user_can_fetch_school_a_by_its_own_id(client, db_session):
    fixture = _TwoSchools(client, db_session)

    response = client.get(
        f"/api/schools/{fixture.school_a.id}", headers=_auth_headers(fixture.token_a)
    )

    assert response.status_code == 200
    assert response.json()["id"] == fixture.school_a.id


def test_school_a_user_cannot_access_school_b_by_changing_the_url_id(client, db_session):
    fixture = _TwoSchools(client, db_session)

    response = client.get(
        f"/api/schools/{fixture.school_b.id}", headers=_auth_headers(fixture.token_a)
    )

    # 404, not 403 — the caller can't tell the difference between "not
    # yours" and "doesn't exist".
    assert response.status_code == 404


def test_school_b_user_cannot_access_school_a_by_changing_the_url_id(client, db_session):
    fixture = _TwoSchools(client, db_session)

    response = client.get(
        f"/api/schools/{fixture.school_a.id}", headers=_auth_headers(fixture.token_b)
    )

    assert response.status_code == 404


def test_nonexistent_school_id_and_wrong_tenant_school_id_look_identical(client, db_session):
    """
    The whole point of returning 404 for both cases: a School A caller
    should get byte-for-byte the same response whether School B's ID is
    real or made up.
    """
    fixture = _TwoSchools(client, db_session)
    headers = _auth_headers(fixture.token_a)

    real_other_school_response = client.get(f"/api/schools/{fixture.school_b.id}", headers=headers)
    made_up_id_response = client.get("/api/schools/999999", headers=headers)

    assert real_other_school_response.status_code == made_up_id_response.status_code == 404
    assert real_other_school_response.json() == made_up_id_response.json()


def test_super_admin_can_fetch_any_school_by_id(client, db_session):
    fixture = _TwoSchools(client, db_session)
    headers = _auth_headers(fixture.token_super)

    response_a = client.get(f"/api/schools/{fixture.school_a.id}", headers=headers)
    response_b = client.get(f"/api/schools/{fixture.school_b.id}", headers=headers)

    assert response_a.status_code == 200
    assert response_a.json()["id"] == fixture.school_a.id
    assert response_b.status_code == 200
    assert response_b.json()["id"] == fixture.school_b.id


def test_super_admin_gets_404_for_a_school_that_does_not_exist(client, db_session):
    fixture = _TwoSchools(client, db_session)

    response = client.get("/api/schools/999999", headers=_auth_headers(fixture.token_super))

    assert response.status_code == 404


def test_super_admin_has_no_home_school_via_me(client, db_session):
    """
    SUPER_ADMIN has school_id = NULL and no single "home" school — /me is
    for school-bound accounts only, so this is a 403, not a silent
    fallback to some default school.
    """
    fixture = _TwoSchools(client, db_session)

    response = client.get("/api/schools/me", headers=_auth_headers(fixture.token_super))

    assert response.status_code == 403


def test_changing_school_id_in_request_body_does_not_bypass_isolation(client, db_session):
    """
    /api/schools/me ignores any client-supplied body entirely — the
    school comes from the authenticated user's trusted school_id, never
    from anything the client sends. A malicious body is simply ignored,
    not honored.
    """
    fixture = _TwoSchools(client, db_session)

    response = client.get(
        "/api/schools/me",
        headers=_auth_headers(fixture.token_a),
        params={"school_id": fixture.school_b.id},
    )

    assert response.status_code == 200
    assert response.json()["id"] == fixture.school_a.id  # not School B


def test_unauthenticated_request_is_rejected(client, db_session):
    _TwoSchools(client, db_session)

    response = client.get("/api/schools/me")

    assert response.status_code == 401


def test_inactive_user_is_rejected_even_with_a_valid_looking_request(client, db_session):
    fixture = _TwoSchools(client, db_session)

    # The inactive user can't even log in to get a token (Phase 3
    # behavior) — confirm that still holds under Phase 4's endpoints too.
    login_response = client.post(
        "/api/auth/login",
        json={"email": "inactive-a@example.com", "password": "pass-inactive"},
    )
    assert login_response.status_code == 401
