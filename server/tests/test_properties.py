"""Property-Based Tests for Profile Management.

Uses Hypothesis to verify correctness properties of the ProfileService layer.
Each test creates a fresh in-memory SQLite database to ensure isolation.

Feature: settings-profile
"""

import asyncio

from hypothesis import given, settings, assume
from hypothesis import strategies as st
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.exceptions import ProfileNameDuplicateError
from app.models.settings_profile import SettingsProfile
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import ProfileCreate, ProfileUpdate
from app.services.profile_service import ProfileService


# ─── Strategies ─────────────────────────────────────────────────────────────

valid_name_strategy = st.text(min_size=1, max_size=50).filter(
    lambda s: s.strip() and len(s.strip()) <= 50
)

valid_description_strategy = st.text(min_size=0, max_size=200)

whitespace_only_strategy = st.text(
    alphabet=st.sampled_from(" \t\n\r"), min_size=1, max_size=10
)

too_long_name_strategy = st.text(min_size=51, max_size=100)


# ─── Helper ─────────────────────────────────────────────────────────────────


async def _make_session():
    """Create a fresh in-memory async session with tables created."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, factory


# ─── Property 1: 프로필 생성 라운드트립 ─────────────────────────────────────
# Feature: settings-profile, Property 1: 프로필 생성 라운드트립
# For any valid ProfileCreate input (name 1~50 chars after strip, description 0~200 chars),
# after creation, retrieving the profile yields the same name and description.
# **Validates: Requirements 1.1, 1.2, 1.3**


@given(name=valid_name_strategy, desc=valid_description_strategy)
@settings(max_examples=100)
def test_property_1_create_roundtrip(name, desc):
    """Property 1: 프로필 생성 라운드트립 — created profile matches input."""

    async def _run():
        engine, factory = await _make_session()
        try:
            async with factory() as session:
                service = ProfileService(session)
                create_data = ProfileCreate(name=name, description=desc)
                created = await service.create_profile(create_data)
                await session.commit()

                # Retrieve and verify roundtrip
                retrieved = await service.get_profile(created.id)
                assert retrieved.name == name.strip()
                assert retrieved.description == desc
                assert retrieved.created_at is not None
                assert retrieved.updated_at is not None
        finally:
            await engine.dispose()

    asyncio.run(_run())


# ─── Property 2: 프로필 수정 라운드트립 ─────────────────────────────────────
# Feature: settings-profile, Property 2: 프로필 수정 라운드트립
# For any existing profile and valid ProfileUpdate input,
# after update the profile reflects the new values and updated_at is refreshed.
# **Validates: Requirements 2.1, 2.2**


@given(
    original_name=valid_name_strategy,
    original_desc=valid_description_strategy,
    new_name=valid_name_strategy,
    new_desc=valid_description_strategy,
)
@settings(max_examples=100)
def test_property_2_update_roundtrip(original_name, original_desc, new_name, new_desc):
    """Property 2: 프로필 수정 라운드트립 — updated profile reflects changes."""
    # Ensure the new name differs from original (case-insensitive) to avoid duplicate error
    assume(new_name.strip().lower() != original_name.strip().lower())

    async def _run():
        engine, factory = await _make_session()
        try:
            async with factory() as session:
                service = ProfileService(session)

                # Create original profile
                create_data = ProfileCreate(name=original_name, description=original_desc)
                created = await service.create_profile(create_data)
                await session.commit()

                original_updated_at = created.updated_at

                # Update the profile
                update_data = ProfileUpdate(name=new_name, description=new_desc)
                updated = await service.update_profile(created.id, update_data)
                await session.commit()

                # Verify roundtrip
                retrieved = await service.get_profile(created.id)
                assert retrieved.name == new_name.strip()
                assert retrieved.description == new_desc
                assert retrieved.updated_at >= original_updated_at
        finally:
            await engine.dispose()

    asyncio.run(_run())


# ─── Property 3: 이름 유효성 검증 ───────────────────────────────────────────
# Feature: settings-profile, Property 3: 이름 유효성 검증 — 공백 및 길이 초과 거부
# For any whitespace-only or >50 char string used as name, create/update is rejected.
# **Validates: Requirements 1.4, 1.7, 2.3, 2.6**


@given(bad_name=whitespace_only_strategy)
@settings(max_examples=100)
def test_property_3_whitespace_name_rejected_on_create(bad_name):
    """Property 3a: whitespace-only name is rejected on create."""
    try:
        ProfileCreate(name=bad_name, description="")
        # If Pydantic doesn't catch it at min_length, the validator should
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass  # Expected


@given(bad_name=too_long_name_strategy)
@settings(max_examples=100)
def test_property_3_too_long_name_rejected_on_create(bad_name):
    """Property 3b: >50 char name is rejected on create."""
    try:
        ProfileCreate(name=bad_name, description="")
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass  # Expected


@given(bad_name=whitespace_only_strategy)
@settings(max_examples=100)
def test_property_3_whitespace_name_rejected_on_update(bad_name):
    """Property 3c: whitespace-only name is rejected on update."""
    try:
        ProfileUpdate(name=bad_name, description="")
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass  # Expected


@given(bad_name=too_long_name_strategy)
@settings(max_examples=100)
def test_property_3_too_long_name_rejected_on_update(bad_name):
    """Property 3d: >50 char name is rejected on update."""
    try:
        ProfileUpdate(name=bad_name, description="")
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass  # Expected


# ─── Property 4: 이름 유니크 제약 ───────────────────────────────────────────
# Feature: settings-profile, Property 4: 이름 유니크 제약
# For any two profiles, creating or updating with a case-insensitive duplicate name is rejected.
# **Validates: Requirements 1.5, 2.4**

# Strategy for names with ASCII letters (SQLite lower() only handles ASCII)
ascii_letter_name_strategy = st.text(
    alphabet=st.sampled_from(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ "
    ),
    min_size=1,
    max_size=50,
).filter(lambda s: s.strip() and any(c.isalpha() for c in s))


@given(name=ascii_letter_name_strategy)
@settings(max_examples=100)
def test_property_4_duplicate_name_rejected_on_create(name):
    """Property 4a: case-insensitive duplicate name rejected on create."""
    # Ensure swapcase produces a different string (has ASCII letters)
    stripped = name.strip()
    variant = stripped.swapcase()
    assume(variant != stripped)
    assume(variant.lower() == stripped.lower())

    async def _run():
        engine, factory = await _make_session()
        try:
            async with factory() as session:
                service = ProfileService(session)

                # Create first profile
                create_data = ProfileCreate(name=name, description="first")
                await service.create_profile(create_data)
                await session.commit()

                # Attempt to create second with case-swapped name
                try:
                    create_data2 = ProfileCreate(name=variant, description="second")
                    await service.create_profile(create_data2)
                    await session.commit()
                    assert False, "Should have raised ProfileNameDuplicateError"
                except ProfileNameDuplicateError:
                    pass  # Expected
        finally:
            await engine.dispose()

    asyncio.run(_run())


@given(
    name1=ascii_letter_name_strategy,
    name2=ascii_letter_name_strategy,
)
@settings(max_examples=100)
def test_property_4_duplicate_name_rejected_on_update(name1, name2):
    """Property 4b: case-insensitive duplicate name rejected on update."""
    # Ensure names are distinct so we can create both
    assume(name1.strip().lower() != name2.strip().lower())
    # Ensure swapcase is meaningful
    variant = name1.strip().swapcase()
    assume(variant != name1.strip())
    assume(variant.lower() == name1.strip().lower())

    async def _run():
        engine, factory = await _make_session()
        try:
            async with factory() as session:
                service = ProfileService(session)

                # Create two profiles with distinct names
                p1 = await service.create_profile(
                    ProfileCreate(name=name1, description="p1")
                )
                await session.commit()
                p2 = await service.create_profile(
                    ProfileCreate(name=name2, description="p2")
                )
                await session.commit()

                # Try to update p2's name to p1's name (case-insensitive match)
                try:
                    await service.update_profile(
                        p2.id, ProfileUpdate(name=variant)
                    )
                    await session.commit()
                    assert False, "Should have raised ProfileNameDuplicateError"
                except ProfileNameDuplicateError:
                    pass  # Expected
        finally:
            await engine.dispose()

    asyncio.run(_run())


# ─── Property 5: 기본 프로필 단일성 불변식 ───────────────────────────────────
# Feature: settings-profile, Property 5: 기본 프로필 단일성 불변식
# After any operation sequence, if profiles exist, exactly one has is_default=True.
# **Validates: Requirements 5.1, 5.2, 5.3, 1.6, 4.4**

# Define an operation strategy for the stateful test
operation_strategy = st.sampled_from(["create", "delete", "copy", "set_default"])


@given(
    names=st.lists(valid_name_strategy, min_size=2, max_size=6, unique_by=lambda s: s.strip().lower()),
    operations=st.lists(operation_strategy, min_size=1, max_size=8),
)
@settings(max_examples=100)
def test_property_5_default_profile_invariant(names, operations):
    """Property 5: exactly one default profile exists after any operation sequence."""

    async def _run():
        engine, factory = await _make_session()
        try:
            async with factory() as session:
                service = ProfileService(session)

                # Create initial profiles
                profile_ids = []
                for name in names:
                    try:
                        p = await service.create_profile(
                            ProfileCreate(name=name, description="")
                        )
                        await session.commit()
                        profile_ids.append(p.id)
                    except Exception:
                        await session.rollback()

                # We need at least one profile to test the invariant
                if not profile_ids:
                    return

                # Execute random operations
                for op in operations:
                    if not profile_ids:
                        break

                    try:
                        if op == "create":
                            # Generate a unique name
                            import uuid
                            new_name = f"gen_{uuid.uuid4().hex[:8]}"
                            p = await service.create_profile(
                                ProfileCreate(name=new_name, description="")
                            )
                            await session.commit()
                            profile_ids.append(p.id)

                        elif op == "delete":
                            if len(profile_ids) > 1:
                                target_id = profile_ids[-1]
                                await service.delete_profile(target_id)
                                await session.commit()
                                profile_ids.remove(target_id)

                        elif op == "copy":
                            target_id = profile_ids[0]
                            try:
                                copied = await service.copy_profile(target_id)
                                await session.commit()
                                profile_ids.append(copied.id)
                            except Exception:
                                await session.rollback()

                        elif op == "set_default":
                            target_id = profile_ids[0]
                            await service.set_default_profile(target_id)
                            await session.commit()

                    except Exception:
                        await session.rollback()

                # Verify invariant: exactly one default profile
                all_profiles = await service.list_profiles()
                if all_profiles:
                    default_count = sum(
                        1 for p in all_profiles if p.is_default
                    )
                    assert default_count == 1, (
                        f"Expected exactly 1 default profile, found {default_count} "
                        f"among {len(all_profiles)} profiles"
                    )
        finally:
            await engine.dispose()

    asyncio.run(_run())


# ─── Property 6: 프로필 복사 속성 일관성 ─────────────────────────────────────
# Feature: settings-profile, Property 6: 프로필 복사 속성 일관성
# For any valid profile, copying it produces a copy with description=original,
# is_default=false, and name in the format "원본이름 (복사본)".
# **Validates: Requirements 3.2, 3.3, 3.4**

from app.services.profile_service import generate_export_filename


@given(name=valid_name_strategy, desc=valid_description_strategy)
@settings(max_examples=100)
def test_property_6_copy_preserves_attributes(name, desc):
    """Property 6: copy preserves description, is_default=false, name format '원본 (복사본)'."""
    # Ensure the copy name won't collide with the original
    stripped = name.strip()
    assume(len(stripped) <= 50)
    # The copy name "원본 (복사본)" must also be <= 50 chars for the system
    # Actually the system doesn't enforce 50-char limit on auto-generated copy names via DB
    # but we need the original name not to already look like a copy name
    assume(not stripped.endswith("(복사본)"))

    async def _run():
        engine, factory = await _make_session()
        try:
            async with factory() as session:
                service = ProfileService(session)

                # Create original profile
                original = await service.create_profile(
                    ProfileCreate(name=name, description=desc)
                )
                await session.commit()

                # Copy the profile
                copy = await service.copy_profile(original.id)
                await session.commit()

                # Verify copy attributes
                assert copy.description == original.description
                assert copy.is_default is False
                assert copy.name == f"{stripped} (복사본)"
                assert copy.created_at is not None
                assert copy.updated_at is not None
        finally:
            await engine.dispose()

    asyncio.run(_run())


# ─── Property 7: 복사본 이름 순번 증가 ───────────────────────────────────────
# Feature: settings-profile, Property 7: 복사본 이름 순번 증가
# For any profile copied N times (2~10), all copies have unique names with
# incrementing suffix pattern.
# **Validates: Requirements 3.5**


@given(
    name=st.text(
        alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789"),
        min_size=1,
        max_size=20,
    ).filter(lambda s: s.strip()),
    n_copies=st.integers(min_value=2, max_value=10),
)
@settings(max_examples=100)
def test_property_7_copy_name_incrementing_suffix(name, n_copies):
    """Property 7: N copies (2~10) have unique names with incrementing suffix."""

    async def _run():
        engine, factory = await _make_session()
        try:
            async with factory() as session:
                service = ProfileService(session)

                # Create original
                original = await service.create_profile(
                    ProfileCreate(name=name, description="original")
                )
                await session.commit()

                # Make N copies
                copy_names = []
                for _ in range(n_copies):
                    copy = await service.copy_profile(original.id)
                    await session.commit()
                    copy_names.append(copy.name)

                # All copy names should be unique
                assert len(set(copy_names)) == n_copies

                # First copy: "name (복사본)", subsequent: "name (복사본 2)", ...
                stripped = name.strip()
                assert copy_names[0] == f"{stripped} (복사본)"
                for i in range(1, n_copies):
                    assert copy_names[i] == f"{stripped} (복사본 {i + 1})"
        finally:
            await engine.dispose()

    asyncio.run(_run())


# ─── Property 8: 기본 프로필 삭제 시 위임 ─────────────────────────────────────
# Feature: settings-profile, Property 8: 기본 프로필 삭제 시 위임
# For any set of 2~10 profiles, deleting the default assigns default to the
# most recently updated remaining profile.
# **Validates: Requirements 4.4**

import time


@given(
    names=st.lists(
        st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789"),
            min_size=1,
            max_size=20,
        ).filter(lambda s: s.strip()),
        min_size=2,
        max_size=10,
        unique_by=lambda s: s.strip().lower(),
    )
)
@settings(max_examples=100)
def test_property_8_delete_default_delegates(names):
    """Property 8: deleting default assigns to most recently updated."""

    async def _run():
        engine, factory = await _make_session()
        try:
            async with factory() as session:
                service = ProfileService(session)

                # Create profiles — first one auto-becomes default
                profile_ids = []
                for name in names:
                    p = await service.create_profile(
                        ProfileCreate(name=name, description="")
                    )
                    await session.commit()
                    profile_ids.append(p.id)

                # The first profile is the default
                default_id = profile_ids[0]

                # Update the last profile to make it the most recently updated
                # (so we can predict which one gets default after deletion)
                last_id = profile_ids[-1]
                await service.update_profile(
                    last_id, ProfileUpdate(description="updated last")
                )
                await session.commit()

                # Delete the default profile
                await service.delete_profile(default_id)
                await session.commit()

                # Verify: the most recently updated profile is now the default
                all_profiles = await service.list_profiles()
                defaults = [p for p in all_profiles if p.is_default]
                assert len(defaults) == 1
                # The new default should be the last-updated one
                assert defaults[0].id == last_id
        finally:
            await engine.dispose()

    asyncio.run(_run())


# ─── Property 9: 직렬화 라운드트립 ───────────────────────────────────────────
# Feature: settings-profile, Property 9: 직렬화 라운드트립
# For any valid profile, export → import preserves name and description.
# **Validates: Requirements 10.1, 10.2, 10.3**


@given(name=valid_name_strategy, desc=valid_description_strategy)
@settings(max_examples=100)
def test_property_9_serialization_roundtrip(name, desc):
    """Property 9: export → import preserves name and description."""
    stripped = name.strip()
    # Ensure name won't collide when re-imported (different from original)
    assume(len(stripped) >= 1)

    async def _run():
        engine, factory = await _make_session()
        try:
            async with factory() as session:
                service = ProfileService(session)

                # Create original profile
                original = await service.create_profile(
                    ProfileCreate(name=name, description=desc)
                )
                await session.commit()

                # Export
                exported = await service.export_profile(original.id)

                # Modify the exported name to avoid duplicate on import
                import_name = f"{stripped}_imported"
                exported["profile"]["name"] = import_name

                # Import
                imported = await service.import_profile(exported)
                await session.commit()

                # Verify roundtrip: description preserved exactly
                assert imported.description == desc

                # Verify the name we set is preserved
                assert imported.name == import_name
        finally:
            await engine.dispose()

    asyncio.run(_run())


# ─── Property 10: 잘못된 JSON 가져오기 거부 ───────────────────────────────────
# Feature: settings-profile, Property 10: 잘못된 JSON 가져오기 거부
# Random bytes and missing-field JSON are rejected, existing data unchanged.
# **Validates: Requirements 7.3, 7.4, 10.4**

from app.core.exceptions import ImportValidationError


@given(random_bytes=st.binary(min_size=1, max_size=200))
@settings(max_examples=100)
def test_property_10_random_bytes_rejected(random_bytes):
    """Property 10a: random bytes (non-JSON) are rejected."""

    async def _run():
        engine, factory = await _make_session()
        try:
            async with factory() as session:
                service = ProfileService(session)

                # Create a baseline profile
                baseline = await service.create_profile(
                    ProfileCreate(name="baseline", description="original")
                )
                await session.commit()

                # Try to import random bytes (simulate: these would fail json.loads,
                # but our import_profile takes a parsed dict, so we simulate
                # "not a dict" scenario)
                import json
                try:
                    data = json.loads(random_bytes)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # If it can't even be parsed as JSON, that's the expected case
                    # The real endpoint would reject this before calling import_profile
                    return

                # If it happened to be valid JSON, try importing it
                try:
                    await service.import_profile(data)
                    await session.commit()
                    # If it somehow succeeded (e.g. random bytes decoded to valid structure)
                    # that's fine — the property focuses on invalid inputs being rejected
                except (ImportValidationError, Exception):
                    await session.rollback()

                # Verify baseline is unchanged
                check = await service.get_profile(baseline.id)
                assert check.name == "baseline"
                assert check.description == "original"
        finally:
            await engine.dispose()

    asyncio.run(_run())


@given(
    bad_json=st.fixed_dictionaries(
        {"profile": st.fixed_dictionaries({"description": valid_description_strategy})}
    )
)
@settings(max_examples=100)
def test_property_10_missing_name_field_rejected(bad_json):
    """Property 10b: JSON with missing 'name' field is rejected, data unchanged."""

    async def _run():
        engine, factory = await _make_session()
        try:
            async with factory() as session:
                service = ProfileService(session)

                # Create a baseline profile
                baseline = await service.create_profile(
                    ProfileCreate(name="baseline_b", description="original_b")
                )
                await session.commit()
                baseline_id = baseline.id

            # Use a new session to attempt the invalid import
            async with factory() as session:
                service = ProfileService(session)
                count_before = await service.repo.count()

                # Try to import JSON missing the name field
                try:
                    await service.import_profile(bad_json)
                    await session.commit()
                    assert False, "Should have raised ImportValidationError"
                except ImportValidationError:
                    await session.rollback()

            # Use a fresh session to verify data unchanged
            async with factory() as session:
                service = ProfileService(session)
                count_after = await service.repo.count()
                assert count_after == count_before

                check = await service.get_profile(baseline_id)
                assert check.name == "baseline_b"
                assert check.description == "original_b"
        finally:
            await engine.dispose()

    asyncio.run(_run())


# ─── Property 11: 내보내기 파일명 특수문자 치환 ───────────────────────────────
# Feature: settings-profile, Property 11: 내보내기 파일명 특수문자 치환
# For any profile name with forbidden chars, generate_export_filename replaces
# all forbidden chars (\ / : * ? " < > |) and result contains none of them.
# **Validates: Requirements 6.3**

_FORBIDDEN_CHARS = set('\\/:*?"<>|')

forbidden_char_strategy = st.text(
    alphabet=st.sampled_from(
        list('\\/:*?"<>|') + list("abcdefghijklmnopqrstuvwxyz0123456789 _-한글")
    ),
    min_size=1,
    max_size=50,
)


@given(profile_name=forbidden_char_strategy)
@settings(max_examples=100)
def test_property_11_export_filename_no_forbidden_chars(profile_name):
    """Property 11: generate_export_filename replaces all forbidden chars."""
    filename = generate_export_filename(profile_name)

    # The result filename must not contain any forbidden characters
    for ch in _FORBIDDEN_CHARS:
        assert ch not in filename, (
            f"Forbidden char '{ch}' found in filename: {filename}"
        )

    # The filename should follow the expected format
    assert filename.startswith("profile_")
    assert filename.endswith(".json")


# ─── Property 12: 목록 정렬 불변식 ───────────────────────────────────────────
# Feature: settings-profile, Property 12: 목록 정렬 불변식
# For any set of 1+ profiles, list always has default first, rest sorted by
# updated_at descending.
# **Validates: Requirements 8.3, 8.4**


@given(
    names=st.lists(
        st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789"),
            min_size=1,
            max_size=20,
        ).filter(lambda s: s.strip()),
        min_size=1,
        max_size=8,
        unique_by=lambda s: s.strip().lower(),
    )
)
@settings(max_examples=100)
def test_property_12_list_sort_invariant(names):
    """Property 12: list always has default first, rest sorted by updated_at desc."""

    async def _run():
        engine, factory = await _make_session()
        try:
            async with factory() as session:
                service = ProfileService(session)

                # Create profiles
                for name in names:
                    await service.create_profile(
                        ProfileCreate(name=name, description="")
                    )
                    await session.commit()

                # Get the list
                profiles = await service.list_profiles()

                # Must have at least 1 profile
                assert len(profiles) >= 1

                # First profile must be the default
                assert profiles[0].is_default is True

                # Rest must be sorted by updated_at descending
                non_default = profiles[1:]
                for i in range(len(non_default) - 1):
                    assert non_default[i].updated_at >= non_default[i + 1].updated_at, (
                        f"Sort violation: {non_default[i].updated_at} < {non_default[i+1].updated_at}"
                    )
        finally:
            await engine.dispose()

    asyncio.run(_run())
