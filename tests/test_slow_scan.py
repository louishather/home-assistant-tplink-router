"""Fork: everything except status/clients (and LTE/SMS) is read on the slow poll interval."""
import asyncio
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock

from custom_components.tplink_router.const import DEFAULT_SLOW_SCAN_INTERVAL
from custom_components.tplink_router.coordinator import collect_status

from test_coordinator import _bare_coordinator

LOG = logging.getLogger("test")
SLOW_GETTERS = [
    "get_vpn_status", "get_vpn_client_status", "get_port_status", "get_ipv4_reservations",
    "get_ipv4_dhcp_leases", "led_status", "get_access_control", "get_blocked_devices",
]


def _router():
    router = Mock()
    router.get_status.return_value = "STATUS"
    for name in SLOW_GETTERS:
        getattr(router, name).return_value = "NEW"
    return router


def _collect(router, slow):
    return collect_status(
        router, None, None, "OLD_VPN", "OLD_VPNC", ["OLD_PORT"], ["OLD_RES"], LOG,
        led_status=False, access_control="OLD_AC", blocked_devices=["OLD_BLOCKED"],
        dhcp_leases=["OLD_LEASE"], slow=slow,
    )


def test_default_slow_interval_is_five_minutes():
    assert DEFAULT_SLOW_SCAN_INTERVAL == 300


def test_fast_poll_reads_only_status_and_keeps_the_rest():
    router = _router()
    result = _collect(router, slow=False)
    assert result[0] == "STATUS"
    assert result[3:6] == ("OLD_VPN", "OLD_VPNC", ["OLD_PORT"])
    assert result[7] == ["OLD_RES"] and result[12] == ["OLD_LEASE"]
    assert result[9] is False and result[10] == "OLD_AC" and result[11] == ["OLD_BLOCKED"]
    for name in SLOW_GETTERS:
        getattr(router, name).assert_not_called()


def test_slow_poll_reads_everything():
    router = _router()
    result = _collect(router, slow=True)
    assert result[7] == "NEW" and result[12] == "NEW" and result[11] == "NEW"
    for name in SLOW_GETTERS:
        getattr(router, name).assert_called_once()


def _coordinator(**overrides):
    coord, router = _bare_coordinator(slow_scan_interval_seconds=300, **overrides)
    router.authorize.side_effect = None
    router.get_status.return_value = "STATUS"
    coord.reservations = ["OLD_RES"]
    router.get_ipv4_reservations.return_value = ["NEW_RES"]
    return coord, router


def test_coordinator_reads_slow_data_first_then_every_interval():
    coord, router = _coordinator()
    asyncio.run(coord._async_update_data())  # first update: slow
    asyncio.run(coord._async_update_data())  # within 5 minutes: fast
    assert router.get_ipv4_reservations.call_count == 1
    assert router.get_status.call_count == 2
    coord._last_slow_update = datetime.now() - timedelta(seconds=301)
    asyncio.run(coord._async_update_data())
    assert router.get_ipv4_reservations.call_count == 2


def test_an_action_makes_the_next_poll_slow():
    coord, router = _coordinator(_last_slow_update=datetime.now())
    asyncio.run(coord._async_update_data())
    router.get_ipv4_reservations.assert_not_called()
    asyncio.run(coord.reboot())
    asyncio.run(coord._async_update_data())
    router.get_ipv4_reservations.assert_called_once()
    assert coord.slow_refresh_requested is False


def test_failed_slow_poll_stays_due():
    coord, router = _coordinator()
    router.get_status.side_effect = [ValueError("Cannot authorize! boom"), "STATUS"]
    try:
        asyncio.run(coord._async_update_data())
    except Exception:
        pass
    assert getattr(coord, "_last_slow_update", None) is None
    asyncio.run(coord._async_update_data())
    router.get_ipv4_reservations.assert_called_once()
