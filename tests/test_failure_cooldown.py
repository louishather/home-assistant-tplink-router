"""Fork: after a failed update, don't log in to the router again until the cooldown has passed."""
import asyncio
from datetime import datetime, timedelta

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.tplink_router.const import DEFAULT_FAILURE_COOLDOWN

from test_coordinator import _bare_coordinator


def test_default_cooldown_is_two_minutes():
    assert DEFAULT_FAILURE_COOLDOWN == 120


def test_failed_update_starts_cooldown_and_skips_logins():
    coord, router = _bare_coordinator(failure_cooldown_seconds=120)
    with pytest.raises(Exception, match="Cannot authorize"):
        asyncio.run(coord._async_update_data())
    assert router.authorize.call_count == 1
    assert coord.cooldown_until > datetime.now() + timedelta(seconds=110)

    # Polls inside the cooldown fail without touching the router
    for _ in range(3):
        with pytest.raises(UpdateFailed, match="after a failed update"):
            asyncio.run(coord._async_update_data())
    assert router.authorize.call_count == 1


def test_cooldown_expires_and_login_is_tried_again():
    coord, router = _bare_coordinator(
        failure_cooldown_seconds=120, cooldown_until=datetime.now() - timedelta(seconds=1)
    )
    router.authorize.side_effect = None
    asyncio.run(coord._async_update_data())
    assert router.authorize.call_count == 1
    assert coord.cooldown_until is None


def test_retryable_failures_use_all_retries_before_the_cooldown():
    coord, router = _bare_coordinator(failure_cooldown_seconds=60)
    router.authorize.side_effect = TimeoutError("timed out")
    with pytest.raises(TimeoutError):
        asyncio.run(coord._async_update_data())
    assert router.authorize.call_count == 3
    assert coord.cooldown_until is not None


def test_zero_turns_the_cooldown_off():
    coord, router = _bare_coordinator(failure_cooldown_seconds=0)
    for _ in range(2):
        with pytest.raises(Exception, match="Cannot authorize"):
            asyncio.run(coord._async_update_data())
    assert router.authorize.call_count == 2
    assert getattr(coord, "cooldown_until", None) is None


def test_manual_requests_are_not_blocked_by_the_cooldown():
    coord, router = _bare_coordinator(
        failure_cooldown_seconds=120, cooldown_until=datetime.now() + timedelta(seconds=100)
    )
    router.authorize.side_effect = None
    asyncio.run(coord.reboot())
    router.reboot.assert_called_once()
