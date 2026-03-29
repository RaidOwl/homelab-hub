"""Tests for inventory export/import API."""

from __future__ import annotations

from tests.factories import create_hardware


def test_export_returns_json_structure(client):
    r = client.get("/api/inventory/export")
    assert r.status_code == 200
    data = r.get_json()
    for key in (
        "hardware",
        "vms",
        "apps",
        "storage",
        "networks",
        "misc",
        "documents",
    ):
        assert key in data
        assert isinstance(data[key], list)


def test_import_post_allowed_and_round_trip(client):
    create_hardware(name="RoundTripHost", ip_address="10.0.0.50")

    export = client.get("/api/inventory/export")
    assert export.status_code == 200
    payload = export.get_json()
    assert len(payload["hardware"]) == 1
    assert payload["hardware"][0]["name"] == "RoundTripHost"

    imp = client.post("/api/inventory/import", json=payload)
    assert imp.status_code == 200
    assert imp.get_json()["message"] == "Database imported successfully"

    again = client.get("/api/inventory/export")
    assert again.status_code == 200
    restored = again.get_json()
    assert len(restored["hardware"]) == 1
    assert restored["hardware"][0]["name"] == "RoundTripHost"
