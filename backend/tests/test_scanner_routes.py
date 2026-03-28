"""Integration tests for scanner API (scan_manager mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tests.factories import create_app_service, create_hardware, create_vm


@pytest.fixture
def mock_scan_manager(monkeypatch):
    mgr = MagicMock()
    mgr.start_discovery.return_value = "scan-discover-1"
    mgr.start_portscan.return_value = "scan-port-1"
    mgr.start_identify.return_value = "scan-identify-1"
    mgr.start_probe_http.return_value = "scan-probe-1"
    mgr.get_scan.return_value = None
    monkeypatch.setattr("app.routes.scanner.scan_manager", mgr)
    return mgr


def test_interfaces_ok(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.scanner.list_local_subnets",
        lambda: [{"label": "eth0", "subnet": "10.0.0.0/24"}],
    )
    r = client.get("/api/scanner/interfaces")
    assert r.status_code == 200
    data = r.get_json()
    assert data["data"][0]["subnet"] == "10.0.0.0/24"


def test_discover_starts_scan(client, mock_scan_manager):
    r = client.post("/api/scanner/discover", json={"subnet": "192.168.1.0/24"})
    assert r.status_code == 202
    body = r.get_json()
    assert body["scan_id"] == "scan-discover-1"
    mock_scan_manager.start_discovery.assert_called_once_with("192.168.1.0/24")


def test_discover_requires_subnet(client):
    r = client.post("/api/scanner/discover", json={})
    assert r.status_code == 400


def test_portscan_starts_scan(client, mock_scan_manager):
    r = client.post(
        "/api/scanner/portscan",
        json={"target_ip": "10.0.0.5", "port_range": "22,80"},
    )
    assert r.status_code == 202
    mock_scan_manager.start_portscan.assert_called_once_with("10.0.0.5", "22,80")


def test_portscan_default_range(client, mock_scan_manager):
    r = client.post("/api/scanner/portscan", json={"target_ip": "10.0.0.5"})
    assert r.status_code == 202
    mock_scan_manager.start_portscan.assert_called_once_with("10.0.0.5", "1-1024")


def test_identify_starts_scan(client, mock_scan_manager):
    r = client.post("/api/scanner/identify", json={"target_ip": "192.168.0.15"})
    assert r.status_code == 202
    body = r.get_json()
    assert body["scan_id"] == "scan-identify-1"
    mock_scan_manager.start_identify.assert_called_once_with("192.168.0.15")


def test_identify_requires_target_ip(client):
    r = client.post("/api/scanner/identify", json={})
    assert r.status_code == 400


def test_identify_invalid_ip(client):
    r = client.post("/api/scanner/identify", json={"target_ip": "not-an-ip"})
    assert r.status_code == 400


def test_probe_http_starts_scan(client, mock_scan_manager):
    r = client.post(
        "/api/scanner/probe-http",
        json={"target_ip": "192.168.0.10", "port": 8443, "https": True},
    )
    assert r.status_code == 202
    body = r.get_json()
    assert body["scan_id"] == "scan-probe-1"
    mock_scan_manager.start_probe_http.assert_called_once_with("192.168.0.10", 8443, True)


def test_probe_http_https_defaults_false(client, mock_scan_manager):
    r = client.post(
        "/api/scanner/probe-http",
        json={"target_ip": "10.0.0.1", "port": 80},
    )
    assert r.status_code == 202
    mock_scan_manager.start_probe_http.assert_called_once_with("10.0.0.1", 80, False)


def test_probe_http_requires_target_ip(client):
    r = client.post("/api/scanner/probe-http", json={"port": 80})
    assert r.status_code == 400


def test_probe_http_requires_port(client):
    r = client.post("/api/scanner/probe-http", json={"target_ip": "192.168.1.1"})
    assert r.status_code == 400


def test_probe_http_invalid_port(client):
    r = client.post(
        "/api/scanner/probe-http",
        json={"target_ip": "192.168.1.1", "port": 99999},
    )
    assert r.status_code == 400


def test_probe_http_invalid_ip(client):
    r = client.post(
        "/api/scanner/probe-http",
        json={"target_ip": "not-ip", "port": 443},
    )
    assert r.status_code == 400


def test_status_returns_scan(client, mock_scan_manager):
    mock_scan_manager.get_scan.return_value = {
        "scan_id": "x",
        "type": "discover",
        "status": "completed",
        "progress": 100,
        "results": [],
        "error": None,
        "params": {"subnet": "192.168.0.0/24"},
    }
    r = client.get("/api/scanner/status/x")
    assert r.status_code == 200
    assert r.get_json()["data"]["status"] == "completed"


def test_status_404_unknown(client, mock_scan_manager):
    mock_scan_manager.get_scan.return_value = None
    r = client.get("/api/scanner/status/missing")
    assert r.status_code == 404


def test_import_hardware_creates_and_skips_duplicate(app, client):
    create_hardware(name="Existing", ip_address="192.168.1.1")
    r = client.post(
        "/api/scanner/import/hardware",
        json={
            "hosts": [
                {"ip": "192.168.1.1", "name": "Dup", "mac": None},
                {"ip": "192.168.1.50", "name": "NewHost", "hostname": "new.lan", "mac": "aa:bb:cc:dd:ee:ff"},
            ]
        },
    )
    assert r.status_code == 201
    body = r.get_json()
    assert len(body["created"]) == 1
    assert body["created"][0]["ip_address"] == "192.168.1.50"
    assert len(body["skipped"]) == 1


def test_import_apps_creates_with_hardware_parent(app, client):
    hw = create_hardware(name="Srv", ip_address="10.0.0.2", hostname="srv.lan")
    r = client.post(
        "/api/scanner/import/apps",
        json={
            "hardware_id": hw.id,
            "services": [
                {
                    "name": "Web",
                    "port": 443,
                    "https": True,
                    "description": "nginx",
                }
            ],
        },
    )
    assert r.status_code == 201
    created = r.get_json()["created"]
    assert len(created) == 1
    assert created[0]["port"] == 443
    assert created[0]["hardware_id"] == hw.id


def test_import_apps_skips_duplicate_port(app, client):
    hw = create_hardware(name="Srv", ip_address="10.0.0.2")
    create_app_service(name="Old", hardware_id=hw.id, port=80)
    r = client.post(
        "/api/scanner/import/apps",
        json={
            "hardware_id": hw.id,
            "services": [{"name": "Web", "port": 80, "https": False}],
        },
    )
    assert r.status_code == 201
    assert len(r.get_json()["created"]) == 0
    assert len(r.get_json()["skipped"]) == 1


def test_import_apps_vm_parent(app, client):
    hw = create_hardware(name="H")
    vm = create_vm(hardware_id=hw.id, name="V", ip_address="10.0.0.3", hostname="v.lan")
    r = client.post(
        "/api/scanner/import/apps",
        json={
            "vm_id": vm.id,
            "services": [{"name": "SSH", "port": 22, "https": False}],
        },
    )
    assert r.status_code == 201
    assert r.get_json()["created"][0]["vm_id"] == vm.id
