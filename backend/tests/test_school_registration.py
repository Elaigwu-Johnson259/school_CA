"""
End-to-end tests for POST /api/schools/register — the public new-school
sign-up endpoint.
"""
from app.core.security import verify_password
from app.models.school import School
from app.models.user import User


def _valid_payload(**overrides):
    payload = {
        "school_name": "Greenfield Academy",
        "school_email": "hello@greenfield.edu",
        "phone": "+1-555-0100",
        "address": "1 Greenfield Way",
        "state": "CA",
        "country": "USA",
        "admin_email": "admin@greenfield.edu",
        "password": "StrongPass123!",
    }
    payload.update(overrides)
    return payload


def test_registration_succeeds_and_returns_school_and_admin(client, db_session):
    response = client.post("/api/schools/register", json=_valid_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["message"]
    assert body["school"]["name"] == "Greenfield Academy"
    assert body["school"]["email"] == "hello@greenfield.edu"
    assert body["admin"]["email"] == "admin@greenfield.edu"
    assert body["admin"]["role"] == "SCHOOL_ADMIN"


def test_registration_creates_a_school_row(client, db_session):
    client.post("/api/schools/register", json=_valid_payload())

    school = db_session.query(School).filter(School.email == "hello@greenfield.edu").first()
    assert school is not None
    assert school.name == "Greenfield Academy"


def test_registration_creates_school_admin_linked_to_the_new_school(client, db_session):
    client.post("/api/schools/register", json=_valid_payload())

    school = db_session.query(School).filter(School.email == "hello@greenfield.edu").first()
    admin = db_session.query(User).filter(User.email == "admin@greenfield.edu").first()

    assert admin is not None
    assert admin.role.value == "SCHOOL_ADMIN"
    assert admin.school_id == school.id


def test_registration_hashes_the_password(client, db_session):
    client.post("/api/schools/register", json=_valid_payload())

    admin = db_session.query(User).filter(User.email == "admin@greenfield.edu").first()

    assert admin.hashed_password != "StrongPass123!"
    assert verify_password("StrongPass123!", admin.hashed_password)


def test_registration_response_never_includes_the_password_or_its_hash(client, db_session):
    response = client.post("/api/schools/register", json=_valid_payload())

    body_text = response.text
    assert "StrongPass123!" not in body_text
    assert "hashed_password" not in body_text


def test_newly_registered_admin_can_log_in(client, db_session):
    client.post("/api/schools/register", json=_valid_payload())

    login_response = client.post(
        "/api/auth/login",
        json={"email": "admin@greenfield.edu", "password": "StrongPass123!"},
    )

    assert login_response.status_code == 200
    assert login_response.json()["user"]["role"] == "SCHOOL_ADMIN"


def test_client_cannot_choose_super_admin_role(client, db_session):
    """
    The registration schema has no `role` field at all, so sending one
    is simply ignored by FastAPI/Pydantic — it never reaches the model.
    This proves that even trying doesn't work.
    """
    payload = _valid_payload()
    payload["role"] = "SUPER_ADMIN"

    response = client.post("/api/schools/register", json=payload)

    assert response.status_code == 201
    assert response.json()["admin"]["role"] == "SCHOOL_ADMIN"


def test_client_cannot_choose_arbitrary_school_id(client, db_session):
    """Same idea: `school_id` isn't a field on the schema, so sending one changes nothing."""
    existing_school = School(name="Existing School", email="existing@example.com")
    db_session.add(existing_school)
    db_session.commit()
    db_session.refresh(existing_school)

    payload = _valid_payload()
    payload["school_id"] = existing_school.id

    response = client.post("/api/schools/register", json=payload)

    assert response.status_code == 201
    new_school_id = response.json()["school"]["id"]
    assert new_school_id != existing_school.id

    admin = db_session.query(User).filter(User.email == "admin@greenfield.edu").first()
    assert admin.school_id == new_school_id
    assert admin.school_id != existing_school.id


def test_duplicate_school_email_is_rejected(client, db_session):
    client.post("/api/schools/register", json=_valid_payload())

    response = client.post(
        "/api/schools/register",
        json=_valid_payload(admin_email="someone-else@greenfield.edu"),
    )

    assert response.status_code == 409


def test_duplicate_admin_email_is_rejected(client, db_session):
    client.post("/api/schools/register", json=_valid_payload())

    response = client.post(
        "/api/schools/register",
        json=_valid_payload(school_name="Different School", school_email="different@example.com"),
    )

    assert response.status_code == 409


def test_invalid_registration_data_is_rejected(client, db_session):
    bad_payload = _valid_payload(school_email="not-an-email", password="short")

    response = client.post("/api/schools/register", json=bad_payload)

    assert response.status_code == 422


def test_missing_required_field_is_rejected(client, db_session):
    payload = _valid_payload()
    del payload["school_name"]

    response = client.post("/api/schools/register", json=payload)

    assert response.status_code == 422


def test_failed_registration_leaves_no_partial_records(client, db_session):
    """
    A duplicate admin_email should fail cleanly, leaving neither a new
    School row nor a new User row behind — proving the transaction is
    atomic, not "create school, then try (and fail) to create the admin".
    """
    client.post("/api/schools/register", json=_valid_payload())
    schools_before = db_session.query(School).count()
    users_before = db_session.query(User).count()

    response = client.post(
        "/api/schools/register",
        json=_valid_payload(school_name="Another School", school_email="another@example.com"),
    )
    assert response.status_code == 409

    assert db_session.query(School).count() == schools_before
    assert db_session.query(User).count() == users_before
