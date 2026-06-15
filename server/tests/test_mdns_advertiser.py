"""Tests for mDNS Advertiser module.

Tests cover:
- Service registration and unregistration
- Duplicate server detection logic
- TXT record content verification
- Singleton instance management
"""

import socket
from unittest.mock import MagicMock, patch

import pytest

from app.core.mdns_advertiser import (
    APP_VERSION,
    SERVICE_NAME,
    SERVICE_TYPE,
    DuplicateServerError,
    MDNSAdvertiser,
    _ExistingServerListener,
    get_mdns_advertiser,
    reset_advertiser,
)


@pytest.fixture(autouse=True)
def cleanup_advertiser():
    """Reset singleton advertiser before and after each test."""
    reset_advertiser()
    yield
    reset_advertiser()


@pytest.fixture
def mock_server_id():
    """Mock server identity to return a fixed UUID."""
    with patch("app.core.mdns_advertiser.get_server_id") as mock:
        mock.return_value = "test-uuid-1234-5678-abcd"
        yield mock


class TestMDNSAdvertiserInit:
    """Tests for MDNSAdvertiser initialization."""

    def test_default_port(self):
        """Advertiser uses default port 8741."""
        adv = MDNSAdvertiser()
        assert adv.port == 8741

    def test_custom_port(self):
        """Advertiser accepts a custom port."""
        adv = MDNSAdvertiser(port=9000)
        assert adv.port == 9000

    def test_default_version(self):
        """Advertiser uses APP_VERSION by default."""
        adv = MDNSAdvertiser()
        assert adv.version == APP_VERSION

    def test_custom_version(self):
        """Advertiser accepts a custom version."""
        adv = MDNSAdvertiser(version="1.2.3")
        assert adv.version == "1.2.3"

    def test_not_registered_initially(self):
        """Advertiser is not registered on creation."""
        adv = MDNSAdvertiser()
        assert adv.is_registered is False


class TestServiceRegistration:
    """Tests for service registration and unregistration."""

    @patch("app.core.mdns_advertiser.Zeroconf")
    @patch("app.core.mdns_advertiser.ServiceInfo")
    @patch("app.core.mdns_advertiser.ServiceBrowser")
    def test_start_advertising_registers_service(
        self, mock_browser, mock_service_info_cls, mock_zeroconf_cls, mock_server_id
    ):
        """start_advertising registers service with zeroconf."""
        mock_zc_instance = MagicMock()
        mock_zeroconf_cls.return_value = mock_zc_instance
        mock_info = MagicMock()
        mock_service_info_cls.return_value = mock_info

        adv = MDNSAdvertiser(port=8741)
        adv.start_advertising(check_duplicates=False)

        assert adv.is_registered is True
        # Verify register_service was called
        mock_zc_instance.register_service.assert_called_once_with(mock_info)

    @patch("app.core.mdns_advertiser.Zeroconf")
    @patch("app.core.mdns_advertiser.ServiceInfo")
    @patch("app.core.mdns_advertiser.ServiceBrowser")
    def test_stop_advertising_unregisters_service(
        self, mock_browser, mock_service_info_cls, mock_zeroconf_cls, mock_server_id
    ):
        """stop_advertising unregisters the service."""
        mock_zc_instance = MagicMock()
        mock_zeroconf_cls.return_value = mock_zc_instance
        mock_info = MagicMock()
        mock_service_info_cls.return_value = mock_info

        adv = MDNSAdvertiser(port=8741)
        adv.start_advertising(check_duplicates=False)
        adv.stop_advertising()

        assert adv.is_registered is False
        mock_zc_instance.unregister_service.assert_called_once_with(mock_info)
        mock_zc_instance.close.assert_called_once()

    @patch("app.core.mdns_advertiser.Zeroconf")
    @patch("app.core.mdns_advertiser.ServiceInfo")
    def test_start_advertising_when_already_registered(
        self, mock_service_info_cls, mock_zeroconf_cls, mock_server_id
    ):
        """start_advertising is idempotent when already registered."""
        mock_zc_instance = MagicMock()
        mock_zeroconf_cls.return_value = mock_zc_instance

        adv = MDNSAdvertiser(port=8741)
        adv.start_advertising(check_duplicates=False)
        # Second call should not re-register
        adv.start_advertising(check_duplicates=False)

        assert mock_zc_instance.register_service.call_count == 1

    def test_stop_advertising_when_not_registered(self):
        """stop_advertising is safe to call when not registered."""
        adv = MDNSAdvertiser()
        # Should not raise
        adv.stop_advertising()
        assert adv.is_registered is False


class TestTXTRecordContent:
    """Tests for TXT record properties in the service registration."""

    @patch("app.core.mdns_advertiser.Zeroconf")
    @patch("app.core.mdns_advertiser.ServiceInfo")
    def test_txt_record_contains_server_id(
        self, mock_service_info_cls, mock_zeroconf_cls, mock_server_id
    ):
        """TXT record includes server-id from get_server_id()."""
        mock_zc_instance = MagicMock()
        mock_zeroconf_cls.return_value = mock_zc_instance

        adv = MDNSAdvertiser(port=8741)
        adv.start_advertising(check_duplicates=False)

        # Verify ServiceInfo was constructed with correct properties
        call_kwargs = mock_service_info_cls.call_args
        properties = call_kwargs[1]["properties"] if call_kwargs[1] else call_kwargs[0][4]

        assert properties["server-id"] == "test-uuid-1234-5678-abcd"

    @patch("app.core.mdns_advertiser.Zeroconf")
    @patch("app.core.mdns_advertiser.ServiceInfo")
    def test_txt_record_contains_port(
        self, mock_service_info_cls, mock_zeroconf_cls, mock_server_id
    ):
        """TXT record includes the server port."""
        mock_zc_instance = MagicMock()
        mock_zeroconf_cls.return_value = mock_zc_instance

        adv = MDNSAdvertiser(port=9999)
        adv.start_advertising(check_duplicates=False)

        call_kwargs = mock_service_info_cls.call_args
        properties = call_kwargs[1]["properties"] if call_kwargs[1] else call_kwargs[0][4]

        assert properties["port"] == "9999"

    @patch("app.core.mdns_advertiser.Zeroconf")
    @patch("app.core.mdns_advertiser.ServiceInfo")
    def test_txt_record_contains_version(
        self, mock_service_info_cls, mock_zeroconf_cls, mock_server_id
    ):
        """TXT record includes the application version."""
        mock_zc_instance = MagicMock()
        mock_zeroconf_cls.return_value = mock_zc_instance

        adv = MDNSAdvertiser(port=8741, version="2.0.0")
        adv.start_advertising(check_duplicates=False)

        call_kwargs = mock_service_info_cls.call_args
        properties = call_kwargs[1]["properties"] if call_kwargs[1] else call_kwargs[0][4]

        assert properties["version"] == "2.0.0"

    @patch("app.core.mdns_advertiser.Zeroconf")
    @patch("app.core.mdns_advertiser.ServiceInfo")
    def test_service_type_is_correct(
        self, mock_service_info_cls, mock_zeroconf_cls, mock_server_id
    ):
        """Service is registered with the correct service type."""
        mock_zc_instance = MagicMock()
        mock_zeroconf_cls.return_value = mock_zc_instance

        adv = MDNSAdvertiser(port=8741)
        adv.start_advertising(check_duplicates=False)

        call_args = mock_service_info_cls.call_args[0]
        assert call_args[0] == SERVICE_TYPE
        assert call_args[1] == SERVICE_NAME


class TestDuplicateServerDetection:
    """Tests for duplicate server detection logic."""

    @patch("app.core.mdns_advertiser.time.sleep")
    @patch("app.core.mdns_advertiser.ServiceBrowser")
    @patch("app.core.mdns_advertiser.Zeroconf")
    def test_check_existing_servers_no_duplicates(
        self, mock_zeroconf_cls, mock_browser_cls, mock_sleep, mock_server_id
    ):
        """check_existing_servers returns empty list when no servers found."""
        mock_zc_instance = MagicMock()
        mock_zeroconf_cls.return_value = mock_zc_instance

        adv = MDNSAdvertiser(port=8741)
        result = adv.check_existing_servers(timeout=0.1)

        assert result == []
        mock_zc_instance.close.assert_called_once()

    @patch("app.core.mdns_advertiser.Zeroconf")
    @patch("app.core.mdns_advertiser.ServiceInfo")
    @patch("app.core.mdns_advertiser.ServiceBrowser")
    @patch("app.core.mdns_advertiser.time.sleep")
    def test_start_advertising_raises_on_duplicate(
        self,
        mock_sleep,
        mock_browser_cls,
        mock_service_info_cls,
        mock_zeroconf_cls,
        mock_server_id,
    ):
        """start_advertising raises DuplicateServerError when another server exists."""
        mock_zc_instance = MagicMock()
        mock_zeroconf_cls.return_value = mock_zc_instance

        # Simulate finding an existing server during check
        adv = MDNSAdvertiser(port=8741)

        # Mock check_existing_servers to return a different server
        with patch.object(
            adv,
            "check_existing_servers",
            return_value=[
                {"server_id": "other-server-uuid", "host": "192.168.1.100", "port": 8741}
            ],
        ):
            with pytest.raises(DuplicateServerError) as exc_info:
                adv.start_advertising(check_duplicates=True)

            assert exc_info.value.server_id == "other-server-uuid"
            assert exc_info.value.host == "192.168.1.100"
            assert exc_info.value.port == 8741

        assert adv.is_registered is False

    @patch("app.core.mdns_advertiser.Zeroconf")
    @patch("app.core.mdns_advertiser.ServiceInfo")
    def test_start_advertising_ignores_same_server_id(
        self, mock_service_info_cls, mock_zeroconf_cls, mock_server_id
    ):
        """start_advertising does not treat same server_id as duplicate."""
        mock_zc_instance = MagicMock()
        mock_zeroconf_cls.return_value = mock_zc_instance

        adv = MDNSAdvertiser(port=8741)

        # Mock check_existing_servers to return our own server
        with patch.object(
            adv,
            "check_existing_servers",
            return_value=[
                {
                    "server_id": "test-uuid-1234-5678-abcd",
                    "host": "192.168.1.50",
                    "port": 8741,
                }
            ],
        ):
            adv.start_advertising(check_duplicates=True)

        assert adv.is_registered is True

    @patch("app.core.mdns_advertiser.Zeroconf")
    @patch("app.core.mdns_advertiser.ServiceInfo")
    def test_start_advertising_skip_duplicate_check(
        self, mock_service_info_cls, mock_zeroconf_cls, mock_server_id
    ):
        """start_advertising can skip duplicate check."""
        mock_zc_instance = MagicMock()
        mock_zeroconf_cls.return_value = mock_zc_instance

        adv = MDNSAdvertiser(port=8741)
        adv.start_advertising(check_duplicates=False)

        assert adv.is_registered is True


class TestDuplicateServerError:
    """Tests for the DuplicateServerError exception."""

    def test_error_attributes(self):
        """DuplicateServerError stores server details."""
        err = DuplicateServerError(
            server_id="abc-123", host="192.168.1.10", port=8741
        )
        assert err.server_id == "abc-123"
        assert err.host == "192.168.1.10"
        assert err.port == 8741

    def test_error_message(self):
        """DuplicateServerError has descriptive message."""
        err = DuplicateServerError(
            server_id="abc-123", host="192.168.1.10", port=8741
        )
        msg = str(err)
        assert "abc-123" in msg
        assert "192.168.1.10" in msg
        assert "8741" in msg


class TestExistingServerListener:
    """Tests for the _ExistingServerListener helper class."""

    def test_add_service_records_server_info(self):
        """add_service extracts server info from ServiceInfo."""
        listener = _ExistingServerListener()

        # Create a mock Zeroconf that returns service info
        mock_zc = MagicMock()
        mock_info = MagicMock()
        mock_info.parsed_addresses.return_value = ["192.168.1.200"]
        mock_info.port = 8741
        mock_info.properties = {
            b"server-id": b"found-server-id",
            b"port": b"8741",
            b"version": b"0.1.0",
        }
        mock_zc.get_service_info.return_value = mock_info

        listener.add_service(mock_zc, SERVICE_TYPE, "some_service")

        assert len(listener.found_servers) == 1
        assert listener.found_servers[0]["server_id"] == "found-server-id"
        assert listener.found_servers[0]["host"] == "192.168.1.200"
        assert listener.found_servers[0]["port"] == 8741

    def test_add_service_handles_missing_info(self):
        """add_service handles case where service info is None."""
        listener = _ExistingServerListener()

        mock_zc = MagicMock()
        mock_zc.get_service_info.return_value = None

        listener.add_service(mock_zc, SERVICE_TYPE, "some_service")

        assert len(listener.found_servers) == 0

    def test_remove_service_is_noop(self):
        """remove_service does not crash."""
        listener = _ExistingServerListener()
        listener.remove_service(MagicMock(), SERVICE_TYPE, "some_service")
        assert len(listener.found_servers) == 0

    def test_update_service_is_noop(self):
        """update_service does not crash."""
        listener = _ExistingServerListener()
        listener.update_service(MagicMock(), SERVICE_TYPE, "some_service")
        assert len(listener.found_servers) == 0


class TestSingleton:
    """Tests for singleton instance management."""

    def test_get_mdns_advertiser_returns_singleton(self):
        """get_mdns_advertiser returns same instance on multiple calls."""
        adv1 = get_mdns_advertiser(port=8741)
        adv2 = get_mdns_advertiser(port=8741)
        assert adv1 is adv2

    def test_reset_advertiser_clears_singleton(self):
        """reset_advertiser allows creating a new instance."""
        adv1 = get_mdns_advertiser(port=8741)
        reset_advertiser()
        adv2 = get_mdns_advertiser(port=8741)
        assert adv1 is not adv2

    @patch("app.core.mdns_advertiser.Zeroconf")
    @patch("app.core.mdns_advertiser.ServiceInfo")
    def test_reset_advertiser_stops_active_service(
        self, mock_service_info_cls, mock_zeroconf_cls, mock_server_id
    ):
        """reset_advertiser stops advertising if active."""
        mock_zc_instance = MagicMock()
        mock_zeroconf_cls.return_value = mock_zc_instance

        adv = get_mdns_advertiser(port=8741)
        adv.start_advertising(check_duplicates=False)
        assert adv.is_registered is True

        reset_advertiser()
        # After reset, old instance should be stopped
        mock_zc_instance.unregister_service.assert_called_once()


class TestLocalIP:
    """Tests for local IP address detection."""

    @patch("app.core.mdns_advertiser.Zeroconf")
    @patch("app.core.mdns_advertiser.ServiceInfo")
    def test_local_ip_used_in_service_info(
        self, mock_service_info_cls, mock_zeroconf_cls, mock_server_id
    ):
        """Service registration uses a resolved local IP address."""
        mock_zc_instance = MagicMock()
        mock_zeroconf_cls.return_value = mock_zc_instance

        adv = MDNSAdvertiser(port=8741)
        adv.start_advertising(check_duplicates=False)

        # Verify addresses were passed to ServiceInfo
        call_kwargs = mock_service_info_cls.call_args[1]
        addresses = call_kwargs.get("addresses", [])
        # Should have at least one address (4-byte packed IP)
        assert len(addresses) >= 1
        # Each address should be 4 bytes (IPv4)
        for addr in addresses:
            assert len(addr) == 4

    @patch("socket.socket")
    @patch("app.core.mdns_advertiser.Zeroconf")
    @patch("app.core.mdns_advertiser.ServiceInfo")
    def test_fallback_to_localhost_on_socket_error(
        self, mock_service_info_cls, mock_zeroconf_cls, mock_socket_cls, mock_server_id
    ):
        """Falls back to 127.0.0.1 when socket fails."""
        mock_zc_instance = MagicMock()
        mock_zeroconf_cls.return_value = mock_zc_instance

        # Make socket raise an error
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = OSError("Network unreachable")
        mock_socket_cls.return_value = mock_sock

        adv = MDNSAdvertiser(port=8741)
        adv.start_advertising(check_duplicates=False)

        # Verify ServiceInfo was called with 127.0.0.1 packed address
        call_kwargs = mock_service_info_cls.call_args[1]
        addresses = call_kwargs.get("addresses", [])
        assert socket.inet_aton("127.0.0.1") in addresses
