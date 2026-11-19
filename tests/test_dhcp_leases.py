import asyncio
import logging
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from custom_components.tplink_router import async_setup_entry
from custom_components.tplink_router.const import DOMAIN
from custom_components.tplink_router.coordinator import TPLinkRouterCoordinator

from custom_components.tplink_router.coordinator import collect_status
from custom_components.tplink_router.sensor import TPLinkRouterDHCPLeasesSensor

from test_coordinator import FakeRouter
from test_setup_isolation import FakeHass, PlainClient, _entry

LOG = logging.getLogger("test")


def _sensor(leases):
    coordinator = Mock()
    coordinator.dhcp_leases = leases
    sensor = TPLinkRouterDHCPLeasesSensor.__new__(TPLinkRouterDHCPLeasesSensor)
    sensor.coordinator = coordinator
    return sensor


def test_leases_sensor_native_value_and_attributes():
    lease = SimpleNamespace(
        macaddr="AA-BB-CC-DD-EE-FF", ipaddr="192.168.1.50", hostname="phone", lease_time="1:23:45"
    )
    sensor = _sensor([lease])
    assert sensor.native_value == 1
    assert sensor.extra_state_attributes == {
        "leases": [{"mac": "AA-BB-CC-DD-EE-FF", "ip": "192.168.1.50", "hostname": "phone", "lease_time": "1:23:45"}]
    }


def test_leases_sensor_none_and_empty():
    sensor = _sensor(None)
    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {"leases": []}
    sensor.coordinator.dhcp_leases = []
    assert sensor.native_value == 0


def test_leases_sensor_blank_hostname_and_lease_time():
    lease = SimpleNamespace(macaddr="AA-BB-CC-DD-EE-FF", ipaddr="192.168.1.50", hostname=None, lease_time=None)
    assert _sensor([lease]).extra_state_attributes["leases"][0] == {
        "mac": "AA-BB-CC-DD-EE-FF", "ip": "192.168.1.50", "hostname": "", "lease_time": ""
    }


def test_leases_attribute_is_not_recorded():
    assert "leases" in TPLinkRouterDHCPLeasesSensor._unrecorded_attributes


def test_collect_status_reads_leases_when_enabled():
    router = FakeRouter()
    router.get_ipv4_dhcp_leases = Mock(return_value=["LEASE"])
    result = collect_status(router, None, None, None, None, None, None, LOG, dhcp_leases=[])
    assert result[-1] == ["LEASE"]


def test_collect_status_skips_leases_when_disabled():
    router = FakeRouter()
    router.get_ipv4_dhcp_leases = Mock(return_value=["LEASE"])
    result = collect_status(router, None, None, None, None, None, None, LOG)
    assert result[-1] is None
    router.get_ipv4_dhcp_leases.assert_not_called()


def test_collect_status_keeps_last_leases_on_failure():
    router = FakeRouter()
    router.get_ipv4_dhcp_leases = Mock(side_effect=RuntimeError("boom"))
    result = collect_status(router, None, None, None, None, None, None, LOG, dhcp_leases=["OLD"])
    assert result[-1] == ["OLD"]
    # A failing leases read doesn't break the rest of the update
    assert result[0] is not None


def _setup(client, **entry_data):
    hass = FakeHass()
    entry = _entry(**entry_data)
    with patch.object(
        TPLinkRouterCoordinator, "get_client_by_class", return_value=Mock(return_value=client)
    ), patch(
        "custom_components.tplink_router.collect_mesh_nodes", return_value=None
    ), patch(
        "custom_components.tplink_router.register_services"
    ), patch(
        "custom_components.tplink_router._async_add_listeners"
    ), patch(
        "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.__init__",
        return_value=None,
    ), patch(
        "custom_components.tplink_router.device_registry.async_get",
        return_value=Mock(),
    ):
        assert asyncio.run(async_setup_entry(hass, entry)) is True
    return hass.data[DOMAIN][entry.entry_id]


def test_setup_probes_leases_by_default():
    client = PlainClient()
    client.get_ipv4_dhcp_leases = Mock(return_value=["LEASE"])
    assert _setup(client).dhcp_leases == ["LEASE"]


@pytest.mark.parametrize("unsupported", ["option_off", "no_method", "fails"])
def test_setup_leaves_leases_off(unsupported):
    client = PlainClient()
    data = {}
    if unsupported == "option_off":
        client.get_ipv4_dhcp_leases = Mock(return_value=["LEASE"])
        data["support_dhcp_leases"] = False
    elif unsupported == "fails":
        client.get_ipv4_dhcp_leases = Mock(side_effect=RuntimeError("no DHCP page"))
    assert _setup(client, **data).dhcp_leases is None
    if unsupported == "option_off":
        client.get_ipv4_dhcp_leases.assert_not_called()
