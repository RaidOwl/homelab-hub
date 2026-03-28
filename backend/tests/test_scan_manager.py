"""Tests for ScanManager threading and status."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

from app.services.scan_manager import ScanManager
from app.services.scanner import NetworkScanner


def test_start_discovery_completes_with_results():
    mock_scanner = MagicMock(spec=NetworkScanner)
    mock_scanner.discover_hosts.return_value = [
        {"ip": "192.168.1.1", "mac": None, "hostname": None, "vendor": None},
    ]
    mgr = ScanManager(scanner=mock_scanner, ttl_seconds=60)
    scan_id = mgr.start_discovery("192.168.1.0/24")
    assert scan_id
    deadline = time.time() + 5
    state = None
    while time.time() < deadline:
        state = mgr.get_scan(scan_id)
        if state and state["status"] == "completed":
            break
        time.sleep(0.05)
    assert state is not None
    assert state["status"] == "completed"
    assert state["progress"] == 100
    assert len(state["results"]) == 1
    assert state["results"][0]["ip"] == "192.168.1.1"


def test_start_portscan_failure_sets_failed():
    mock_scanner = MagicMock(spec=NetworkScanner)
    mock_scanner.scan_ports.side_effect = RuntimeError("nmap missing")

    mgr = ScanManager(scanner=mock_scanner, ttl_seconds=60)
    scan_id = mgr.start_portscan("10.0.0.1", "22")
    deadline = time.time() + 5
    state = None
    while time.time() < deadline:
        state = mgr.get_scan(scan_id)
        if state and state["status"] == "failed":
            break
        time.sleep(0.05)
    assert state is not None
    assert state["status"] == "failed"
    assert "nmap" in (state["error"] or "")


def test_get_scan_unknown_returns_none():
    mgr = ScanManager(scanner=MagicMock(spec=NetworkScanner))
    assert mgr.get_scan("00000000-0000-0000-0000-000000000000") is None


def test_start_identify_completes_with_results():
    mock_scanner = MagicMock(spec=NetworkScanner)
    mock_scanner.identify_host.return_value = {
        "hostname": "box.lan",
        "mac_address": "00:11:22:33:44:55",
        "os": "FreeBSD",
    }
    mgr = ScanManager(scanner=mock_scanner, ttl_seconds=60)
    scan_id = mgr.start_identify("192.168.1.10")
    assert scan_id
    deadline = time.time() + 5
    state = None
    while time.time() < deadline:
        state = mgr.get_scan(scan_id)
        if state and state["status"] == "completed":
            break
        time.sleep(0.05)
    assert state is not None
    assert state["status"] == "completed"
    assert state["type"] == "identify"
    assert state["progress"] == 100
    assert len(state["results"]) == 1
    assert state["results"][0]["hostname"] == "box.lan"
    mock_scanner.identify_host.assert_called_once_with("192.168.1.10")


def test_start_identify_failure_sets_failed():
    mock_scanner = MagicMock(spec=NetworkScanner)
    mock_scanner.identify_host.side_effect = RuntimeError("nmap failed")

    mgr = ScanManager(scanner=mock_scanner, ttl_seconds=60)
    scan_id = mgr.start_identify("10.0.0.1")
    deadline = time.time() + 5
    state = None
    while time.time() < deadline:
        state = mgr.get_scan(scan_id)
        if state and state["status"] == "failed":
            break
        time.sleep(0.05)
    assert state is not None
    assert state["status"] == "failed"
    assert "nmap" in (state["error"] or "")


def test_start_probe_http_completes_with_results():
    mock_scanner = MagicMock(spec=NetworkScanner)
    mock_scanner.probe_http_headers.return_value = {
        "server": "nginx",
        "x_powered_by": None,
        "title": "App",
        "application_name": None,
        "og_site_name": None,
        "generator": None,
        "suggested_name": "App",
        "error": None,
    }
    mgr = ScanManager(scanner=mock_scanner, ttl_seconds=60)
    scan_id = mgr.start_probe_http("192.168.1.20", 8080, False)
    assert scan_id
    deadline = time.time() + 5
    state = None
    while time.time() < deadline:
        state = mgr.get_scan(scan_id)
        if state and state["status"] == "completed":
            break
        time.sleep(0.05)
    assert state is not None
    assert state["status"] == "completed"
    assert state["type"] == "probe_http"
    assert state["progress"] == 100
    assert len(state["results"]) == 1
    assert state["results"][0]["suggested_name"] == "App"
    mock_scanner.probe_http_headers.assert_called_once_with("192.168.1.20", 8080, False)


def test_start_probe_http_failure_sets_failed():
    mock_scanner = MagicMock(spec=NetworkScanner)
    mock_scanner.probe_http_headers.side_effect = RuntimeError("probe failed")

    mgr = ScanManager(scanner=mock_scanner, ttl_seconds=60)
    scan_id = mgr.start_probe_http("10.0.0.2", 443, True)
    deadline = time.time() + 5
    state = None
    while time.time() < deadline:
        state = mgr.get_scan(scan_id)
        if state and state["status"] == "failed":
            break
        time.sleep(0.05)
    assert state is not None
    assert state["status"] == "failed"
    assert "probe" in (state["error"] or "")
