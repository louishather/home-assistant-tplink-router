"""Fork: held login, and leaving the router alone when another login takes the session."""
import asyncio
from datetime import datetime, timedelta

import pytest
import requests
from homeassistant.exceptions import HomeAssistantError
from tplinkrouterc6u import ClientError, ClientException
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.tplink_router.const import DEFAULT_HOLD_SESSION, DEFAULT_YIELD_MINUTES
from custom_components.tplink_router.coordinator import SessionTakenOver

from test_coordinator import _bare_coordinator


def _held(**overrides):
    settings = dict(
        hold_session=True, yield_minutes=3, _session_used=None, _update_interval_seconds=45,
        failure_cooldown_seconds=120,
    )
    settings.update(overrides)
    coord, router = _bare_coordinator(**settings)
    router.authorize.side_effect = None
    router.get_status.return_value = "STATUS"
    return coord, router


def test_defaults():
    assert DEFAULT_HOLD_SESSION is False
    assert DEFAULT_YIELD_MINUTES == 3


def test_held_session_logs_in_once_and_never_logs_out():
    coord, router = _held()
    for _ in range(3):
        asyncio.run(coord._async_update_data())
    assert router.authorize.call_count == 1
    router.logout.assert_not_called()
    assert router.get_status.call_count == 3


def test_actions_share_the_held_session():
    coord, router = _held()
    asyncio.run(coord._async_update_data())
    asyncio.run(coord.reboot())
    assert router.authorize.call_count == 1
    router.reboot.assert_called_once()


def test_takeover_leaves_the_router_alone_for_the_yield_time():
    coord, router = _held()
    asyncio.run(coord._async_update_data())
    # Someone logs in to the web page: HA's next request on the old session is refused
    router.get_status.side_effect = ClientError("TplinkRouter - Response with error; errorcode timeout")
    with pytest.raises(UpdateFailed, match="Another login took over"):
        asyncio.run(coord._async_update_data())
    assert router.authorize.call_count == 1  # no retry, no new login
    assert coord.yield_until > datetime.now() + timedelta(minutes=2, seconds=50)
    with pytest.raises(UpdateFailed, match="Leaving the router alone"):
        asyncio.run(coord._async_update_data())
    # Actions from HA don't log in either while the web page has the router
    with pytest.raises(HomeAssistantError, match="Someone else is logged in"):
        asyncio.run(coord.reboot())
    router.reboot.assert_not_called()
    assert router.authorize.call_count == 1

    # After the wait: log in again and carry on
    router.get_status.side_effect = None
    coord.yield_until = datetime.now() - timedelta(seconds=1)
    asyncio.run(coord._async_update_data())
    assert router.authorize.call_count == 2


def test_failure_on_a_fresh_login_is_an_ordinary_failure():
    coord, router = _held()
    router.get_status.side_effect = ClientError("Cannot authorize! boom")
    with pytest.raises(Exception, match="Cannot authorize"):
        asyncio.run(coord._async_update_data())
    # Normal failed-update cooldown, not the takeover wait
    assert coord.cooldown_until < datetime.now() + timedelta(seconds=121)


def test_network_error_on_a_held_session_is_not_a_takeover():
    coord, router = _held(retries=1)
    asyncio.run(coord._async_update_data())
    router.get_status.side_effect = requests.exceptions.ConnectionError("unreachable")
    with pytest.raises(requests.exceptions.ConnectionError):
        asyncio.run(coord._async_update_data())
    assert coord._session_used is None  # next attempt logs in again


def test_idle_session_is_replaced_not_reported_as_a_takeover():
    coord, router = _held(_session_used=datetime.now() - timedelta(minutes=10))
    asyncio.run(coord._async_update_data())
    assert router.authorize.call_count == 1


def test_zero_yield_minutes_retries_at_the_next_update():
    coord, router = _held(yield_minutes=0)
    asyncio.run(coord._async_update_data())
    router.get_status.side_effect = ClientError("errorcode timeout")
    with pytest.raises(UpdateFailed):
        asyncio.run(coord._async_update_data())
    assert getattr(coord, "yield_until", None) is None


def test_close_session_logs_out_once():
    coord, router = _held()
    asyncio.run(coord._async_update_data())
    coord.close_session()
    coord.close_session()
    router.logout.assert_called_once()


def test_default_mode_still_logs_in_and_out_each_update():
    coord, router = _bare_coordinator()
    router.authorize.side_effect = None
    asyncio.run(coord._async_update_data())
    asyncio.run(coord._async_update_data())
    assert router.authorize.call_count == 2
    assert router.logout.call_count == 2


def test_session_taken_over_is_its_own_error():
    assert issubclass(SessionTakenOver, Exception)


def test_library_refusal_on_a_held_session_is_not_a_takeover():
    coord, router = _held()
    asyncio.run(coord._async_update_data())
    router.add_ipv4_reservation.side_effect = ClientException("A reservation for MAC X already exists")
    with pytest.raises(ClientException, match="already exists"):
        asyncio.run(coord.add_ipv4_reservation("aa:bb:cc:dd:ee:ff", "10.250.5.120"))
    assert getattr(coord, "cooldown_until", None) is None


def test_action_during_takeover_fails_clearly_and_starts_the_wait():
    coord, router = _held()
    asyncio.run(coord._async_update_data())
    router.reboot.side_effect = ClientError("Response with error")
    with pytest.raises(HomeAssistantError, match="Someone else is logged in"):
        asyncio.run(coord.reboot())
    assert coord.yield_until > datetime.now() + timedelta(minutes=2)


def test_failed_update_wait_does_not_block_actions():
    coord, router = _held(cooldown_until=datetime.now() + timedelta(seconds=100))
    asyncio.run(coord.reboot())
    router.reboot.assert_called_once()
