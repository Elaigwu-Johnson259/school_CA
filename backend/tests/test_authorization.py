"""
Unit tests for the require_roles() authorization dependency.

Tested directly (without going through HTTP) by calling the inner
dependency function with fake User objects, since Phase 3 doesn't add any
role-protected endpoints of its own yet — require_roles() is a foundation
for endpoints later phases will build.
"""
from types import SimpleNamespace

from fastapi import HTTPException
import pytest

from app.api.deps import require_roles
from app.models.enums import UserRole


def _fake_user(role: UserRole):
    return SimpleNamespace(role=role)


def test_require_roles_allows_matching_role():
    dependency = require_roles(UserRole.SCHOOL_ADMIN)
    user = _fake_user(UserRole.SCHOOL_ADMIN)

    result = dependency(current_user=user)

    assert result is user


def test_require_roles_allows_any_of_multiple_roles():
    dependency = require_roles(UserRole.SCHOOL_ADMIN, UserRole.TEACHER)

    assert dependency(current_user=_fake_user(UserRole.TEACHER)) is not None
    assert dependency(current_user=_fake_user(UserRole.SCHOOL_ADMIN)) is not None


def test_require_roles_rejects_non_matching_role_with_403():
    dependency = require_roles(UserRole.SUPER_ADMIN)
    user = _fake_user(UserRole.STUDENT)

    with pytest.raises(HTTPException) as exc_info:
        dependency(current_user=user)

    assert exc_info.value.status_code == 403
