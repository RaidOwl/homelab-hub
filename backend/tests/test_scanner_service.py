"""Unit tests for NetworkScanner (nmap mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import nmap

from app.services.scanner import (
    NetworkScanner,
    _infer_os_from_services,
    _is_host_alive,
    _read_arp_cache,
    _resolve_hostname,
    list_local_subnets,
    validate_subnet,
    validate_target_ip,
)


class _HostView:
    """Mimics nmap host entry: .state() and dict-like keys."""

    def __init__(self, data: dict) -> None:
        self._data = data

    def state(self) -> str:
        return self._data.get("state", "unknown")

    def __getitem__(self, key: str):
        return self._data[key]

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def __contains__(self, key: object) -> bool:
        return key in self._data


class FakePortScanner:
    """Mimics nmap.PortScanner interface used by NetworkScanner."""

    def __init__(self, all_hosts, host_data):
        self._all_hosts = all_hosts
        self._host_data = {h: _HostView(d) for h, d in host_data.items()}
        self.scan_calls = []

    def scan(self, hosts, arguments):
        self.scan_calls.append((hosts, arguments))

    def all_hosts(self):
        return list(self._all_hosts)

    def __getitem__(self, host):
        return self._host_data[host]


def test_validate_subnet_invalid():
    with pytest.raises(ValueError):
        validate_subnet("not-a-network")


def test_validate_subnet_valid():
    validate_subnet("192.168.1.0/24")


def test_validate_target_ip_invalid():
    with pytest.raises(ValueError):
        validate_target_ip("999.1.1.1")


def test_discover_hosts_parses_nmap_output(monkeypatch):
    host_data = {
        "192.168.1.10": {
            "state": "up",
            "addresses": {"ipv4": "192.168.1.10", "mac": "AA:BB:CC:DD:EE:FF"},
            "vendor": {"AA:BB:CC:DD:EE:FF": "Acme Inc"},
            "hostnames": [{"name": "router.lan"}],
        },
        "192.168.1.20": {"state": "down"},
    }
    fake = FakePortScanner(["192.168.1.10", "192.168.1.20"], host_data)

    class Factory:
        def __call__(self):
            return fake

    monkeypatch.setattr("app.services.scanner._is_host_alive", lambda ip: True)
    monkeypatch.setattr("app.services.scanner._resolve_hostname", lambda ip: None)

    scanner = NetworkScanner(port_scanner_class=Factory())
    hosts = scanner.discover_hosts("192.168.1.0/24")
    assert len(hosts) == 1
    assert hosts[0]["ip"] == "192.168.1.10"
    assert hosts[0]["mac"] == "AA:BB:CC:DD:EE:FF"
    assert hosts[0]["hostname"] == "router.lan"
    assert hosts[0]["vendor"] == "Acme Inc"
    args = fake.scan_calls[0][1]
    assert "-sn" in args and "-PR" in args and "-PE" in args and "-PS22,80,443,8080" in args
    assert "-PA80" in args and "--max-retries 2" in args and "-T3" in args


def test_discover_hosts_uses_conservative_nmap_flags():
    host_data = {
        "192.168.0.1": {
            "state": "up",
            "addresses": {"ipv4": "192.168.0.1", "mac": "00:00:00:00:00:01"},
        },
    }
    fake = FakePortScanner(["192.168.0.1"], host_data)
    scanner = NetworkScanner(port_scanner_class=lambda: fake)
    scanner.discover_hosts("192.168.0.0/24")
    args = fake.scan_calls[0][1]
    assert "-PR" in args and "-PE" in args and "-PS" in args and "-T3" in args and "--max-retries" in args


def test_is_host_alive_ping_succeeds(monkeypatch):
    monkeypatch.setattr(
        "app.services.scanner.subprocess.run",
        MagicMock(return_value=MagicMock(returncode=0)),
    )
    assert _is_host_alive("192.168.1.1") is True


def test_is_host_alive_ping_fails_tcp_fallback(monkeypatch):
    monkeypatch.setattr(
        "app.services.scanner.subprocess.run",
        MagicMock(return_value=MagicMock(returncode=1)),
    )

    class _Conn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    monkeypatch.setattr(
        "app.services.scanner.socket.create_connection",
        lambda _addr, timeout=0.5: _Conn(),
    )
    assert _is_host_alive("10.0.0.5") is True


def test_is_host_alive_both_fail(monkeypatch):
    monkeypatch.setattr(
        "app.services.scanner.subprocess.run",
        MagicMock(return_value=MagicMock(returncode=1)),
    )
    monkeypatch.setattr(
        "app.services.scanner.socket.create_connection",
        MagicMock(side_effect=OSError("refused")),
    )
    assert _is_host_alive("10.0.0.99") is False


def test_discover_filters_dead_hosts_without_mac(monkeypatch):
    host_data = {
        "192.168.1.1": {"state": "up", "addresses": {"ipv4": "192.168.1.1"}},
        "192.168.1.2": {
            "state": "up",
            "addresses": {"ipv4": "192.168.1.2", "mac": "11:22:33:44:55:66"},
        },
    }
    fake = FakePortScanner(["192.168.1.1", "192.168.1.2"], host_data)
    scanner = NetworkScanner(port_scanner_class=lambda: fake)
    monkeypatch.setattr("app.services.scanner._is_host_alive", lambda ip: False)
    monkeypatch.setattr("app.services.scanner._resolve_hostname", lambda ip: None)
    hosts = scanner.discover_hosts("192.168.1.0/24")
    assert len(hosts) == 1
    assert hosts[0]["ip"] == "192.168.1.2"


def test_discover_keeps_hosts_with_mac_even_if_tcp_fails(monkeypatch):
    host_data = {
        "10.0.0.7": {
            "state": "up",
            "addresses": {"ipv4": "10.0.0.7", "mac": "AA:AA:AA:AA:AA:AA"},
            "hostnames": [],
        },
    }
    fake = FakePortScanner(["10.0.0.7"], host_data)
    scanner = NetworkScanner(port_scanner_class=lambda: fake)
    monkeypatch.setattr("app.services.scanner._is_host_alive", lambda ip: False)
    monkeypatch.setattr("app.services.scanner._resolve_hostname", lambda ip: None)
    hosts = scanner.discover_hosts("10.0.0.0/24")
    assert len(hosts) == 1
    assert hosts[0]["ip"] == "10.0.0.7"


def test_resolve_hostname_via_socket(monkeypatch):
    monkeypatch.setattr(
        "app.services.scanner.socket.gethostbyaddr",
        lambda ip: ("mybox.lan", [], [ip]),
    )
    assert _resolve_hostname("192.168.1.5") == "mybox.lan"


def test_resolve_hostname_fallback_to_nmap(monkeypatch):
    host_data = {
        "10.0.0.1": {
            "state": "up",
            "addresses": {"ipv4": "10.0.0.1", "mac": "01:02:03:04:05:06"},
            "hostnames": [{"name": "from-nmap"}],
        },
    }
    fake = FakePortScanner(["10.0.0.1"], host_data)
    scanner = NetworkScanner(port_scanner_class=lambda: fake)

    def _boom(_ip):
        raise AssertionError("_resolve_hostname must not run when nmap set hostname")

    monkeypatch.setattr("app.services.scanner._resolve_hostname", _boom)
    hosts = scanner.discover_hosts("10.0.0.0/24")
    assert hosts[0]["hostname"] == "from-nmap"


def test_resolve_hostname_none_when_both_fail(monkeypatch):
    host_data = {
        "10.0.0.99": {"state": "up", "addresses": {"ipv4": "10.0.0.99"}},
    }
    fake = FakePortScanner(["10.0.0.99"], host_data)
    scanner = NetworkScanner(port_scanner_class=lambda: fake)
    monkeypatch.setattr("app.services.scanner._is_host_alive", lambda ip: True)
    monkeypatch.setattr("app.services.scanner._resolve_hostname", lambda ip: None)
    hosts = scanner.discover_hosts("10.0.0.0/24")
    assert len(hosts) == 1
    assert hosts[0]["hostname"] is None


def test_discover_hostname_from_socket_when_nmap_empty(monkeypatch):
    host_data = {
        "10.0.0.2": {
            "state": "up",
            "addresses": {"ipv4": "10.0.0.2", "mac": "BB:BB:BB:BB:BB:BB"},
        },
    }
    fake = FakePortScanner(["10.0.0.2"], host_data)
    scanner = NetworkScanner(port_scanner_class=lambda: fake)
    monkeypatch.setattr("app.services.scanner._resolve_hostname", lambda ip: "dhcp-box.lan")
    hosts = scanner.discover_hosts("10.0.0.0/24")
    assert hosts[0]["hostname"] == "dhcp-box.lan"


def test_scan_ports_parses_tcp_open():
    host_data = {
        "10.0.0.5": {
            "state": "up",
            "tcp": {
                22: {"state": "open", "name": "ssh", "product": "OpenSSH", "version": "8.4", "extrainfo": ""},
                80: {"state": "closed", "name": "http"},
            },
        }
    }
    fake = FakePortScanner(["10.0.0.5"], host_data)

    class Factory:
        def __call__(self):
            return fake

    scanner = NetworkScanner(port_scanner_class=Factory())
    rows = scanner.scan_ports("10.0.0.5", "1-1000")
    assert len(rows) == 1
    assert rows[0]["port"] == 22
    assert rows[0]["service_name"] == "ssh"
    assert "OpenSSH" in rows[0]["service_version"]
    assert fake.scan_calls[0][0] == "10.0.0.5"
    assert "-sT" in fake.scan_calls[0][1] and "-p 1-1000" in fake.scan_calls[0][1]


def test_probe_http_headers_parses_title(monkeypatch):
    scanner = NetworkScanner(port_scanner_class=lambda: MagicMock())

    class Resp:
        status_code = 200
        headers = {"Server": "nginx/1.18"}
        text = "<html><title>  My App  </title></html>"

    monkeypatch.setattr(
        "app.services.scanner.requests.get",
        MagicMock(return_value=Resp()),
    )
    out = scanner.probe_http_headers("127.0.0.1", 8080, https=False)
    assert out["server"] == "nginx/1.18"
    assert out["title"] == "My App"
    assert out["application_name"] is None
    assert out["og_site_name"] is None
    assert out["generator"] is None
    assert out["suggested_name"] == "My App"


def test_probe_http_headers_prefers_application_name_over_title(monkeypatch):
    scanner = NetworkScanner(port_scanner_class=lambda: MagicMock())

    class Resp:
        status_code = 200
        headers = {"Server": "nginx/1.18"}
        text = (
            '<html><head>'
            '<meta name="application-name" content="  Grafana  ">'
            "<title>Login</title>"
            "</head></html>"
        )

    monkeypatch.setattr(
        "app.services.scanner.requests.get",
        MagicMock(return_value=Resp()),
    )
    out = scanner.probe_http_headers("10.0.0.1", 3000, https=False)
    assert out["application_name"] == "Grafana"
    assert out["title"] == "Login"
    assert out["suggested_name"] == "Grafana"


def test_probe_http_headers_prefers_og_site_name_over_title(monkeypatch):
    scanner = NetworkScanner(port_scanner_class=lambda: MagicMock())

    class Resp:
        status_code = 200
        headers = {}
        text = (
            '<html><meta property="og:site_name" content="My Homelab">'
            "<title>Dashboard</title></html>"
        )

    monkeypatch.setattr(
        "app.services.scanner.requests.get",
        MagicMock(return_value=Resp()),
    )
    out = scanner.probe_http_headers("192.168.1.1", 80, https=False)
    assert out["og_site_name"] == "My Homelab"
    assert out["title"] == "Dashboard"
    assert out["suggested_name"] == "My Homelab"


def test_probe_http_headers_extracts_generator(monkeypatch):
    scanner = NetworkScanner(port_scanner_class=lambda: MagicMock())

    class Resp:
        status_code = 200
        headers = {"Server": "Apache"}
        text = '<html><meta name="generator" content="WordPress 6.4"><title>Blog</title></html>'

    monkeypatch.setattr(
        "app.services.scanner.requests.get",
        MagicMock(return_value=Resp()),
    )
    out = scanner.probe_http_headers("127.0.0.1", 80, https=False)
    assert out["generator"] == "WordPress 6.4"
    assert out["title"] == "Blog"
    assert out["suggested_name"] == "Blog"


def test_probe_http_headers_falls_back_to_server_when_no_title(monkeypatch):
    scanner = NetworkScanner(port_scanner_class=lambda: MagicMock())

    class Resp:
        status_code = 200
        headers = {"Server": "uvicorn"}
        text = "<html></html>"

    monkeypatch.setattr(
        "app.services.scanner.requests.get",
        MagicMock(return_value=Resp()),
    )
    out = scanner.probe_http_headers("127.0.0.1", 8000, https=False)
    assert out["title"] is None
    assert out["suggested_name"] == "uvicorn"


def test_identify_host_parses_mac_hostname_os(monkeypatch):
    host_data = {
        "10.0.0.5": {
            "state": "up",
            "addresses": {"ipv4": "10.0.0.5", "mac": "AA:BB:CC:DD:EE:FF"},
            "hostnames": [{"name": "device.lan"}],
            "osmatch": [{"name": "Linux 5.4", "accuracy": "95"}],
        },
    }
    fake = FakePortScanner(["10.0.0.5"], host_data)
    monkeypatch.setattr("app.services.scanner._resolve_hostname", lambda ip: None)
    monkeypatch.setattr("app.services.scanner._ping_once", lambda _ip: True)
    monkeypatch.setattr("app.services.scanner._read_arp_cache", lambda _ip: None)

    scanner = NetworkScanner(port_scanner_class=lambda: fake)
    out = scanner.identify_host("10.0.0.5")
    assert out["hostname"] == "device.lan"
    assert out["mac_address"] == "AA:BB:CC:DD:EE:FF"
    assert out["os"] == "Linux 5.4"
    assert fake.scan_calls[0][0] == "10.0.0.5"
    args = fake.scan_calls[0][1]
    assert "-O" in args and "--osscan-guess" in args and "-sV" in args and "-T4" in args
    assert "--host-timeout 50s" in args


def test_identify_host_retries_without_o_on_portscanner_error(monkeypatch):
    host_data = {
        "10.0.0.12": {
            "state": "up",
            "addresses": {"ipv4": "10.0.0.12", "mac": "DE:AD:BE:EF:00:01"},
            "hostnames": [{"name": "retry.lan"}],
            "osmatch": [{"name": "Linux 3.x", "accuracy": "90"}],
        },
    }
    fake = FakePortScanner(["10.0.0.12"], host_data)
    orig_scan = fake.scan
    arg_log: list[str] = []

    def scan_maybe_fail(hosts, arguments):
        arg_log.append(arguments)
        if "-O" in arguments:
            raise nmap.PortScannerError("requires root")
        return orig_scan(hosts, arguments)

    monkeypatch.setattr(fake, "scan", scan_maybe_fail)
    monkeypatch.setattr("app.services.scanner._ping_once", lambda _ip: True)
    monkeypatch.setattr("app.services.scanner._read_arp_cache", lambda _ip: None)

    scanner = NetworkScanner(port_scanner_class=lambda: fake)
    out = scanner.identify_host("10.0.0.12")
    assert out["hostname"] == "retry.lan"
    assert out["mac_address"] == "DE:AD:BE:EF:00:01"
    assert out["os"] == "Linux 3.x"
    assert len(arg_log) == 2
    assert "-O" in arg_log[0]
    assert "-O" not in arg_log[1]
    assert len(fake.scan_calls) == 1


def test_identify_host_fills_mac_from_arp_cache(monkeypatch):
    host_data = {
        "10.0.0.13": {
            "state": "up",
            "addresses": {"ipv4": "10.0.0.13"},
            "hostnames": [],
        },
    }
    fake = FakePortScanner(["10.0.0.13"], host_data)
    monkeypatch.setattr("app.services.scanner._resolve_hostname", lambda _ip: None)
    monkeypatch.setattr("app.services.scanner._ping_once", lambda _ip: True)
    monkeypatch.setattr(
        "app.services.scanner._read_arp_cache",
        lambda ip: "AA:BB:CC:DD:EE:FF" if ip == "10.0.0.13" else None,
    )

    scanner = NetworkScanner(port_scanner_class=lambda: fake)
    out = scanner.identify_host("10.0.0.13")
    assert out["mac_address"] == "AA:BB:CC:DD:EE:FF"


def test_identify_host_infers_os_from_service_banner(monkeypatch):
    host_data = {
        "10.0.0.14": {
            "state": "up",
            "addresses": {"ipv4": "10.0.0.14", "mac": "11:22:33:44:55:66"},
            "hostnames": [],
            "tcp": {
                22: {
                    "state": "open",
                    "name": "ssh",
                    "product": "OpenSSH",
                    "version": "8.4p1",
                    "extrainfo": "Debian 11",
                },
            },
        },
    }
    fake = FakePortScanner(["10.0.0.14"], host_data)
    monkeypatch.setattr("app.services.scanner._resolve_hostname", lambda _ip: None)
    monkeypatch.setattr("app.services.scanner._ping_once", lambda _ip: True)
    monkeypatch.setattr("app.services.scanner._read_arp_cache", lambda _ip: None)

    scanner = NetworkScanner(port_scanner_class=lambda: fake)
    out = scanner.identify_host("10.0.0.14")
    assert out["os"] == "Debian"


def test_read_arp_cache_parses_arp_an(monkeypatch):
    monkeypatch.setattr("app.services.scanner._ping_once", lambda _ip: True)

    def fake_run(cmd, **_kwargs):
        if cmd[0] == "arp":
            return MagicMock(
                returncode=0,
                stdout="? (10.0.0.1) at aa:bb:cc:dd:ee:ff on en0 ifscope [ethernet]\n",
            )
        return MagicMock(returncode=1, stdout="")

    monkeypatch.setattr("app.services.scanner.subprocess.run", fake_run)
    assert _read_arp_cache("10.0.0.1") == "AA:BB:CC:DD:EE:FF"


def test_read_arp_cache_returns_none_when_no_match(monkeypatch):
    monkeypatch.setattr("app.services.scanner._ping_once", lambda _ip: True)

    def fake_run(cmd, **_kwargs):
        if cmd[0] == "arp":
            return MagicMock(returncode=0, stdout="nothing useful here\n")
        return MagicMock(returncode=1, stdout="")

    monkeypatch.setattr("app.services.scanner.subprocess.run", fake_run)
    assert _read_arp_cache("10.0.0.99") is None


def test_infer_os_from_services_debian():
    host = _HostView(
        {
            "state": "up",
            "tcp": {
                22: {
                    "state": "open",
                    "name": "ssh",
                    "product": "OpenSSH",
                    "version": "8.2",
                    "extrainfo": "Debian 11",
                },
            },
        }
    )
    assert _infer_os_from_services(host) == "Debian"


def test_infer_os_from_services_none_for_generic_nginx():
    host = _HostView(
        {
            "state": "up",
            "tcp": {
                80: {
                    "state": "open",
                    "name": "http",
                    "product": "nginx",
                    "version": "1.18",
                    "extrainfo": "",
                },
            },
        }
    )
    assert _infer_os_from_services(host) is None


def test_identify_host_uses_resolve_when_nmap_has_no_hostname(monkeypatch):
    host_data = {
        "10.0.0.6": {
            "state": "up",
            "addresses": {"ipv4": "10.0.0.6", "mac": "11:22:33:44:55:66"},
            "hostnames": [],
        },
    }
    fake = FakePortScanner(["10.0.0.6"], host_data)
    monkeypatch.setattr("app.services.scanner._resolve_hostname", lambda ip: "revdns.lan")
    monkeypatch.setattr("app.services.scanner._ping_once", lambda _ip: True)
    monkeypatch.setattr("app.services.scanner._read_arp_cache", lambda _ip: None)

    scanner = NetworkScanner(port_scanner_class=lambda: fake)
    out = scanner.identify_host("10.0.0.6")
    assert out["hostname"] == "revdns.lan"
    assert out["mac_address"] == "11:22:33:44:55:66"
    assert out["os"] is None


def test_identify_host_down_or_missing_returns_nulls(monkeypatch):
    host_data = {"10.0.0.7": {"state": "down", "addresses": {"ipv4": "10.0.0.7"}}}
    fake = FakePortScanner(["10.0.0.7"], host_data)
    monkeypatch.setattr("app.services.scanner._resolve_hostname", lambda ip: None)
    monkeypatch.setattr("app.services.scanner._ping_once", lambda _ip: True)
    monkeypatch.setattr("app.services.scanner._read_arp_cache", lambda _ip: None)

    scanner = NetworkScanner(port_scanner_class=lambda: fake)
    out = scanner.identify_host("10.0.0.7")
    assert out["hostname"] is None
    assert out["mac_address"] is None
    assert out["os"] is None


def test_identify_host_not_in_all_hosts(monkeypatch):
    fake = FakePortScanner([], {})
    monkeypatch.setattr("app.services.scanner._resolve_hostname", lambda ip: "only.rev")
    monkeypatch.setattr("app.services.scanner._ping_once", lambda _ip: True)
    monkeypatch.setattr("app.services.scanner._read_arp_cache", lambda _ip: None)

    scanner = NetworkScanner(port_scanner_class=lambda: fake)
    out = scanner.identify_host("10.0.0.8")
    assert out["hostname"] == "only.rev"
    assert out["mac_address"] is None
    assert out["os"] is None


def test_list_local_subnets_returns_something_or_empty(monkeypatch):
    # Avoid depending on host OS: stub ip command
    monkeypatch.setattr(
        "app.services.scanner.subprocess.run",
        MagicMock(
            return_value=MagicMock(
                returncode=0,
                stdout='[{"ifname":"eth0","addr_info":[{"family":"inet","local":"192.168.0.5","prefixlen":24}]}]',
            )
        ),
    )
    nets = list_local_subnets()
    assert len(nets) >= 1
    assert any("192.168.0.0/24" in n["subnet"] for n in nets)
