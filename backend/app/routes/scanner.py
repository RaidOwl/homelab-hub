"""LAN discovery, port scan, and bulk import APIs."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..models import AppService, Hardware, VM, db
from ..services.scan_manager import scan_manager
from ..services.scanner import list_local_subnets, validate_subnet, validate_target_ip
from .apps import _set_default_hostname

bp = Blueprint("scanner", __name__, url_prefix="/api/scanner")


def _normalize_mac(mac: str | None) -> str | None:
    if not mac or not str(mac).strip():
        return None
    return str(mac).strip().upper().replace("-", ":")


def _hardware_is_duplicate(ip: str | None, mac: str | None) -> bool:
    if ip:
        if Hardware.query.filter_by(ip_address=ip.strip()).first() is not None:
            return True
    norm = _normalize_mac(mac)
    if norm:
        for row in Hardware.query.filter(Hardware.mac_address.isnot(None)).all():
            if _normalize_mac(row.mac_address) == norm:
                return True
    return False


@bp.route("/interfaces", methods=["GET"])
def get_interfaces():
    data = list_local_subnets()
    return jsonify(data=data)


@bp.route("/discover", methods=["POST"])
def post_discover():
    body = request.get_json()
    if not body or not body.get("subnet"):
        return jsonify(error="subnet is required"), 400
    subnet = str(body["subnet"]).strip()
    try:
        validate_subnet(subnet)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    scan_id = scan_manager.start_discovery(subnet)
    return jsonify(scan_id=scan_id), 202


@bp.route("/portscan", methods=["POST"])
def post_portscan():
    body = request.get_json()
    if not body or not body.get("target_ip"):
        return jsonify(error="target_ip is required"), 400
    target_ip = str(body["target_ip"]).strip()
    try:
        validate_target_ip(target_ip)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    port_range = str(body.get("port_range") or "1-1024").strip()
    scan_id = scan_manager.start_portscan(target_ip, port_range)
    return jsonify(scan_id=scan_id), 202


@bp.route("/identify", methods=["POST"])
def post_identify():
    body = request.get_json()
    if not body or not body.get("target_ip"):
        return jsonify(error="target_ip is required"), 400
    target_ip = str(body["target_ip"]).strip()
    try:
        validate_target_ip(target_ip)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    scan_id = scan_manager.start_identify(target_ip)
    return jsonify(scan_id=scan_id), 202


def _validate_probe_port(raw: object) -> int:
    if raw is None:
        raise ValueError("port is required")
    try:
        port = int(raw)
    except (TypeError, ValueError) as e:
        raise ValueError("port must be an integer") from e
    if port < 1 or port > 65535:
        raise ValueError("port must be between 1 and 65535")
    return port


@bp.route("/probe-http", methods=["POST"])
def post_probe_http():
    body = request.get_json()
    if not body or not body.get("target_ip"):
        return jsonify(error="target_ip is required"), 400
    target_ip = str(body["target_ip"]).strip()
    try:
        validate_target_ip(target_ip)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    try:
        port = _validate_probe_port(body.get("port"))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    https = bool(body.get("https", False))
    scan_id = scan_manager.start_probe_http(target_ip, port, https)
    return jsonify(scan_id=scan_id), 202


@bp.route("/status/<scan_id>", methods=["GET"])
def get_status(scan_id: str):
    state = scan_manager.get_scan(scan_id)
    if state is None:
        return jsonify(data={
            "scan_id": scan_id,
            "status": "expired",
            "progress": 0,
            "results": [],
            "error": None,
            "params": {},
        })
    return jsonify(data=state)


@bp.route("/import/hardware", methods=["POST"])
def import_hardware():
    body = request.get_json()
    if not body or not isinstance(body.get("hosts"), list):
        return jsonify(error="hosts array is required"), 400
    created: list[dict] = []
    skipped: list[dict] = []
    for raw in body["hosts"]:
        if not isinstance(raw, dict):
            skipped.append({"raw": raw, "reason": "invalid entry"})
            continue
        ip = (raw.get("ip") or raw.get("ip_address") or "").strip()
        if not ip:
            skipped.append({**raw, "reason": "missing ip"})
            continue
        if _hardware_is_duplicate(ip, raw.get("mac")):
            skipped.append({**raw, "reason": "duplicate"})
            continue
        name = (raw.get("name") or raw.get("hostname") or ip).strip() or ip
        hostname = (raw.get("hostname") or "").strip() or None
        mac = _normalize_mac(raw.get("mac"))
        hw = Hardware()
        hw.update_from_dict(
            {
                "name": name,
                "hostname": hostname,
                "ip_address": ip,
                "mac_address": mac,
            }
        )
        db.session.add(hw)
        db.session.flush()
        created.append(hw.to_dict())
    db.session.commit()
    return jsonify(created=created, skipped=skipped), 201


@bp.route("/import/apps", methods=["POST"])
def import_apps():
    body = request.get_json()
    if not body or not isinstance(body.get("services"), list):
        return jsonify(error="services array is required"), 400
    hardware_id = body.get("hardware_id")
    vm_id = body.get("vm_id")
    if hardware_id is not None and vm_id is not None:
        return jsonify(error="Specify only one of hardware_id or vm_id"), 400
    if hardware_id is not None:
        if db.session.get(Hardware, int(hardware_id)) is None:
            return jsonify(error="hardware_id not found"), 400
        hardware_id = int(hardware_id)
        vm_id = None
    elif vm_id is not None:
        if db.session.get(VM, int(vm_id)) is None:
            return jsonify(error="vm_id not found"), 400
        vm_id = int(vm_id)
        hardware_id = None
    else:
        return jsonify(error="hardware_id or vm_id is required"), 400

    created: list[dict] = []
    skipped: list[dict] = []

    for raw in body["services"]:
        if not isinstance(raw, dict):
            skipped.append({"raw": raw, "reason": "invalid entry"})
            continue
        port = raw.get("port")
        if port is None:
            skipped.append({**raw, "reason": "missing port"})
            continue
        try:
            port = int(port)
        except (TypeError, ValueError):
            skipped.append({**raw, "reason": "invalid port"})
            continue

        q = AppService.query.filter_by(port=port)
        if hardware_id is not None:
            q = q.filter_by(hardware_id=hardware_id, vm_id=None)
        else:
            q = q.filter_by(vm_id=vm_id, hardware_id=None)
        if q.first() is not None:
            skipped.append({**raw, "reason": "duplicate port for parent"})
            continue

        name = (raw.get("name") or f"Port {port}").strip()
        https = bool(raw.get("https"))
        description = raw.get("description")
        if raw.get("http_probe") and isinstance(raw["http_probe"], dict):
            probe = raw["http_probe"]
            parts = []
            if probe.get("server"):
                parts.append(f"Server: {probe['server']}")
            if probe.get("x_powered_by"):
                parts.append(f"X-Powered-By: {probe['x_powered_by']}")
            if probe.get("title"):
                parts.append(f"Title: {probe['title']}")
            if parts:
                extra = "\n".join(parts)
                description = f"{description}\n{extra}" if description else extra

        app_row = AppService(
            name=name,
            hardware_id=hardware_id,
            vm_id=vm_id,
            port=port,
            https=https,
            description=description,
            hostname=raw.get("hostname"),
            ip_address=raw.get("ip_address"),
        )
        data_for_default = {"hostname": raw.get("hostname")}
        _set_default_hostname(app_row, data_for_default)
        db.session.add(app_row)
        db.session.flush()
        created.append(app_row.to_dict())

    db.session.commit()
    return jsonify(created=created, skipped=skipped), 201
