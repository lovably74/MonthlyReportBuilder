"""mDNS service advertiser for CM Report Server.

Uses the zeroconf library to advertise the server as a
`_cm-report-server._tcp.local.` service on the local network.
Provides duplicate server detection to prevent multiple servers
from running on the same network.
"""

import logging
import socket
import time
from typing import Any

from zeroconf import ServiceBrowser, ServiceInfo, ServiceStateChange, Zeroconf

from app.core.server_identity import get_server_id

logger = logging.getLogger(__name__)

# Service type for mDNS advertisement
SERVICE_TYPE = "_cm-report-server._tcp.local."
SERVICE_NAME = "CM Report Server._cm-report-server._tcp.local."

# App version (sourced from pyproject.toml metadata)
APP_VERSION = "0.1.0"


class DuplicateServerError(Exception):
    """Raised when an existing CM Report Server is detected on the network."""

    def __init__(self, server_id: str, host: str, port: int) -> None:
        self.server_id = server_id
        self.host = host
        self.port = port
        super().__init__(
            f"Duplicate server detected: server_id={server_id}, "
            f"host={host}, port={port}"
        )


class _ExistingServerListener:
    """Listener for detecting existing CM Report Server instances on the network."""

    def __init__(self) -> None:
        self.found_servers: list[dict[str, Any]] = []

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is updated."""

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is removed."""

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a new service is discovered."""
        info = zc.get_service_info(type_, name)
        if info:
            addresses = info.parsed_addresses()
            host = addresses[0] if addresses else "unknown"
            port = info.port
            properties = {
                k.decode("utf-8"): v.decode("utf-8")
                for k, v in info.properties.items()
            }
            server_id = properties.get("server-id", "unknown")
            self.found_servers.append(
                {"server_id": server_id, "host": host, "port": port}
            )


class MDNSAdvertiser:
    """Manages mDNS service registration and unregistration.

    Advertises the CM Report Server on the local network using
    the `_cm-report-server._tcp.local.` service type. Includes
    Server-ID, port, and version in TXT record properties.
    """

    def __init__(self, port: int = 8741, version: str | None = None) -> None:
        """Initialize the mDNS advertiser.

        Args:
            port: The port the server is listening on.
            version: Application version string. Defaults to APP_VERSION.
        """
        self._port = port
        self._version = version or APP_VERSION
        self._zeroconf: Zeroconf | None = None
        self._service_info: ServiceInfo | None = None
        self._is_registered = False

    @property
    def is_registered(self) -> bool:
        """Whether the service is currently registered."""
        return self._is_registered

    @property
    def port(self) -> int:
        """The port being advertised."""
        return self._port

    @property
    def version(self) -> str:
        """The version being advertised."""
        return self._version

    def check_existing_servers(self, timeout: float = 3.0) -> list[dict[str, Any]]:
        """Check for existing CM Report Server instances on the network.

        Args:
            timeout: Seconds to wait for responses from existing servers.

        Returns:
            List of detected servers with their server_id, host, and port.
        """
        zc = Zeroconf()
        listener = _ExistingServerListener()
        try:
            browser = ServiceBrowser(zc, SERVICE_TYPE, listener)  # noqa: F841
            # Wait for the specified timeout for responses
            time.sleep(timeout)
        finally:
            zc.close()

        return listener.found_servers

    def start_advertising(self, check_duplicates: bool = True) -> None:
        """Register the mDNS service on the local network.

        First checks for existing servers on the network (duplicate prevention).
        If a duplicate is found, raises DuplicateServerError.

        Args:
            check_duplicates: Whether to check for existing servers before
                registering. Defaults to True.

        Raises:
            DuplicateServerError: If another server is already running on
                the network.
            RuntimeError: If the service is already registered.
        """
        if self._is_registered:
            logger.warning("mDNS service is already registered.")
            return

        server_id = get_server_id()

        # Check for duplicate servers
        if check_duplicates:
            existing = self.check_existing_servers()
            # Filter out ourselves (same server_id)
            others = [s for s in existing if s["server_id"] != server_id]
            if others:
                other = others[0]
                logger.error(
                    "Duplicate CM Report Server detected on network: "
                    "server_id=%s, host=%s, port=%d",
                    other["server_id"],
                    other["host"],
                    other["port"],
                )
                raise DuplicateServerError(
                    server_id=other["server_id"],
                    host=other["host"],
                    port=other["port"],
                )

        # Build TXT record properties
        properties = {
            "server-id": server_id,
            "port": str(self._port),
            "version": self._version,
        }

        # Get local IP address for registration
        local_ip = self._get_local_ip()

        self._service_info = ServiceInfo(
            SERVICE_TYPE,
            SERVICE_NAME,
            addresses=[socket.inet_aton(local_ip)],
            port=self._port,
            properties=properties,
        )

        self._zeroconf = Zeroconf()
        self._zeroconf.register_service(self._service_info)
        self._is_registered = True

        logger.info(
            "mDNS service registered: type=%s, host=%s, port=%d, "
            "server_id=%s, version=%s",
            SERVICE_TYPE,
            local_ip,
            self._port,
            server_id,
            self._version,
        )

    def stop_advertising(self) -> None:
        """Unregister the mDNS service from the local network."""
        if not self._is_registered or self._zeroconf is None:
            logger.warning("mDNS service is not currently registered.")
            return

        if self._service_info is not None:
            self._zeroconf.unregister_service(self._service_info)

        self._zeroconf.close()
        self._zeroconf = None
        self._service_info = None
        self._is_registered = False

        logger.info("mDNS service unregistered.")

    def _get_local_ip(self) -> str:
        """Get the local IP address of this machine.

        Uses a UDP socket trick to determine the preferred outbound
        IP address without actually sending data.

        Returns:
            Local IP address string.
        """
        try:
            # Create a UDP socket and connect to a non-routable address
            # This doesn't actually send data, but determines the
            # preferred source address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("10.255.255.255", 1))
                ip = s.getsockname()[0]
            finally:
                s.close()
            return ip
        except Exception:
            logger.warning(
                "Could not determine local IP, falling back to 127.0.0.1"
            )
            return "127.0.0.1"


# Module-level singleton instance
_advertiser: MDNSAdvertiser | None = None


def get_mdns_advertiser(port: int = 8741, version: str | None = None) -> MDNSAdvertiser:
    """Get or create the singleton MDNSAdvertiser instance.

    Args:
        port: The port the server is listening on.
        version: Application version string.

    Returns:
        The MDNSAdvertiser singleton instance.
    """
    global _advertiser
    if _advertiser is None:
        _advertiser = MDNSAdvertiser(port=port, version=version)
    return _advertiser


def reset_advertiser() -> None:
    """Reset the singleton advertiser instance.

    Primarily used for testing purposes.
    """
    global _advertiser
    if _advertiser is not None and _advertiser.is_registered:
        _advertiser.stop_advertising()
    _advertiser = None
