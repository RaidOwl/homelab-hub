"""Threaded scan jobs with in-memory status for polling."""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any

from .scanner import NetworkScanner


class ScanManager:
    """Runs discovery/port scans in background threads; TTL eviction for completed scans."""

    def __init__(
        self,
        scanner: NetworkScanner | None = None,
        ttl_seconds: int = 600,
    ) -> None:
        self._scanner = scanner or NetworkScanner()
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._scans: dict[str, dict[str, Any]] = {}

    def _purge_old_unlocked(self) -> None:
        now = time.time()
        dead: list[str] = []
        for sid, meta in self._scans.items():
            if meta.get("status") not in ("completed", "failed"):
                continue
            finished = meta.get("finished_at")
            if finished is not None and now - finished > self._ttl:
                dead.append(sid)
        for sid in dead:
            self._scans.pop(sid, None)

    def start_discovery(self, subnet: str) -> str:
        scan_id = str(uuid.uuid4())
        with self._lock:
            self._purge_old_unlocked()
            self._scans[scan_id] = {
                "type": "discover",
                "status": "running",
                "progress": 0,
                "results": [],
                "error": None,
                "started_at": time.time(),
                "finished_at": None,
                "params": {"subnet": subnet},
            }
        thread = threading.Thread(
            target=self._run_discovery,
            args=(scan_id, subnet),
            daemon=True,
            name=f"discover-{scan_id[:8]}",
        )
        thread.start()
        return scan_id

    def start_portscan(self, target_ip: str, port_range: str = "1-1024") -> str:
        scan_id = str(uuid.uuid4())
        with self._lock:
            self._purge_old_unlocked()
            self._scans[scan_id] = {
                "type": "portscan",
                "status": "running",
                "progress": 0,
                "results": [],
                "error": None,
                "started_at": time.time(),
                "finished_at": None,
                "params": {"target_ip": target_ip, "port_range": port_range},
            }
        thread = threading.Thread(
            target=self._run_portscan,
            args=(scan_id, target_ip, port_range),
            daemon=True,
            name=f"portscan-{scan_id[:8]}",
        )
        thread.start()
        return scan_id

    def start_identify(self, target_ip: str) -> str:
        scan_id = str(uuid.uuid4())
        with self._lock:
            self._purge_old_unlocked()
            self._scans[scan_id] = {
                "type": "identify",
                "status": "running",
                "progress": 0,
                "results": [],
                "error": None,
                "started_at": time.time(),
                "finished_at": None,
                "params": {"target_ip": target_ip},
            }
        thread = threading.Thread(
            target=self._run_identify,
            args=(scan_id, target_ip),
            daemon=True,
            name=f"identify-{scan_id[:8]}",
        )
        thread.start()
        return scan_id

    def start_probe_http(self, target_ip: str, port: int, https: bool) -> str:
        scan_id = str(uuid.uuid4())
        with self._lock:
            self._purge_old_unlocked()
            self._scans[scan_id] = {
                "type": "probe_http",
                "status": "running",
                "progress": 0,
                "results": [],
                "error": None,
                "started_at": time.time(),
                "finished_at": None,
                "params": {"target_ip": target_ip, "port": port, "https": https},
            }
        thread = threading.Thread(
            target=self._run_probe_http,
            args=(scan_id, target_ip, port, https),
            daemon=True,
            name=f"probe-http-{scan_id[:8]}",
        )
        thread.start()
        return scan_id

    def _run_discovery(self, scan_id: str, subnet: str) -> None:
        try:
            with self._lock:
                if scan_id in self._scans:
                    self._scans[scan_id]["progress"] = 10
            hosts = self._scanner.discover_hosts(subnet)
            with self._lock:
                if scan_id in self._scans:
                    self._scans[scan_id]["progress"] = 100
                    self._scans[scan_id]["status"] = "completed"
                    self._scans[scan_id]["results"] = hosts
                    self._scans[scan_id]["finished_at"] = time.time()
        except Exception as e:  # noqa: BLE001 — surface any scanner failure to client
            with self._lock:
                if scan_id in self._scans:
                    self._scans[scan_id]["status"] = "failed"
                    self._scans[scan_id]["error"] = str(e)
                    self._scans[scan_id]["finished_at"] = time.time()

    def _run_portscan(self, scan_id: str, target_ip: str, port_range: str) -> None:
        try:
            with self._lock:
                if scan_id in self._scans:
                    self._scans[scan_id]["progress"] = 20
            rows = self._scanner.scan_ports(target_ip, port_range)
            with self._lock:
                if scan_id in self._scans:
                    self._scans[scan_id]["progress"] = 60
            enriched = self._scanner.enrich_open_ports_with_http(target_ip, rows)
            with self._lock:
                if scan_id in self._scans:
                    self._scans[scan_id]["progress"] = 100
                    self._scans[scan_id]["status"] = "completed"
                    self._scans[scan_id]["results"] = enriched
                    self._scans[scan_id]["finished_at"] = time.time()
        except Exception as e:  # noqa: BLE001
            with self._lock:
                if scan_id in self._scans:
                    self._scans[scan_id]["status"] = "failed"
                    self._scans[scan_id]["error"] = str(e)
                    self._scans[scan_id]["finished_at"] = time.time()

    def _run_identify(self, scan_id: str, target_ip: str) -> None:
        try:
            with self._lock:
                if scan_id in self._scans:
                    self._scans[scan_id]["progress"] = 20
            row = self._scanner.identify_host(target_ip)
            with self._lock:
                if scan_id in self._scans:
                    self._scans[scan_id]["progress"] = 100
                    self._scans[scan_id]["status"] = "completed"
                    self._scans[scan_id]["results"] = [row]
                    self._scans[scan_id]["finished_at"] = time.time()
        except Exception as e:  # noqa: BLE001
            with self._lock:
                if scan_id in self._scans:
                    self._scans[scan_id]["status"] = "failed"
                    self._scans[scan_id]["error"] = str(e)
                    self._scans[scan_id]["finished_at"] = time.time()

    def _run_probe_http(self, scan_id: str, target_ip: str, port: int, https: bool) -> None:
        try:
            with self._lock:
                if scan_id in self._scans:
                    self._scans[scan_id]["progress"] = 50
            row = self._scanner.probe_http_headers(target_ip, port, https)
            with self._lock:
                if scan_id in self._scans:
                    self._scans[scan_id]["progress"] = 100
                    self._scans[scan_id]["status"] = "completed"
                    self._scans[scan_id]["results"] = [row]
                    self._scans[scan_id]["finished_at"] = time.time()
        except Exception as e:  # noqa: BLE001
            with self._lock:
                if scan_id in self._scans:
                    self._scans[scan_id]["status"] = "failed"
                    self._scans[scan_id]["error"] = str(e)
                    self._scans[scan_id]["finished_at"] = time.time()

    def get_scan(self, scan_id: str) -> dict[str, Any] | None:
        with self._lock:
            self._purge_old_unlocked()
            meta = self._scans.get(scan_id)
            if meta is None:
                return None
            return {
                "scan_id": scan_id,
                "type": meta["type"],
                "status": meta["status"],
                "progress": meta["progress"],
                "results": list(meta["results"]),
                "error": meta["error"],
                "params": dict(meta["params"]),
            }


# Singleton used by Flask routes; tests may replace `scan_manager` on the blueprint module.
scan_manager = ScanManager()
