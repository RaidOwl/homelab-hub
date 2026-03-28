"""Network discovery and port scanning via nmap; HTTP probing for service metadata."""

from __future__ import annotations

import ipaddress
import json
import logging
import os
import re
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import nmap
import requests

logger = logging.getLogger(__name__)

# Ports commonly serving HTTP(S) for header/title probing
_HTTP_LIKE_PORTS = frozenset({80, 443, 8080, 8443, 8000, 8888, 3000, 5000, 9000, 9443})


def _normalize_mac(mac: str | None) -> str | None:
    if not mac:
        return None
    m = mac.strip().upper().replace("-", ":")
    return m if m else None


def list_local_subnets() -> list[dict[str, str]]:
    """Return interface labels and CIDR hints for the UI (best-effort)."""
    results: list[dict[str, str]] = []

    try:
        proc = subprocess.run(
            ["ip", "-j", "addr", "show"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout:
            data = json.loads(proc.stdout)
            for iface in data:
                name = iface.get("ifname") or "interface"
                for addr_info in iface.get("addr_info") or []:
                    if addr_info.get("family") != "inet":
                        continue
                    local = addr_info.get("local")
                    prefix = addr_info.get("prefixlen")
                    if not local or prefix is None:
                        continue
                    try:
                        net = ipaddress.ip_network(f"{local}/{prefix}", strict=False)
                        results.append({"label": f"{name}: {net}", "subnet": str(net)})
                    except ValueError:
                        continue
    except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        logger.debug("ip -j addr not usable: %s", e)

    if not results:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.5)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            parts = local_ip.split(".")
            if len(parts) == 4:
                guess = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
                results.append({"label": f"Guess from default route: {guess}", "subnet": guess})
        except OSError as e:
            logger.debug("default route guess failed: %s", e)

    return results


def validate_subnet(subnet: str) -> None:
    """Raise ValueError if subnet is not a valid IPv4 network."""
    try:
        net = ipaddress.ip_network(subnet.strip(), strict=False)
    except ValueError as e:
        raise ValueError(f"Invalid subnet: {subnet}") from e
    if net.version != 4:
        raise ValueError("Only IPv4 networks are supported")


def validate_target_ip(ip: str) -> None:
    try:
        addr = ipaddress.ip_address(ip.strip())
    except ValueError as e:
        raise ValueError(f"Invalid IP: {ip}") from e
    if addr.version != 4:
        raise ValueError("Only IPv4 targets are supported")


def _ping_once(ip: str) -> bool:
    """One ICMP echo via system ping (works without root on most macOS/Linux)."""
    try:
        if sys.platform == "darwin":
            # -W: milliseconds to wait for each reply (BSD ping)
            cmd = ["ping", "-c", "1", "-W", "1000", ip]
        elif os.name == "nt" or sys.platform.startswith("win"):
            cmd = ["ping", "-n", "1", "-w", "1000", ip]
        else:
            # BusyBox (Alpine) and iputils: -w is overall deadline in seconds
            cmd = ["ping", "-c", "1", "-w", "2", ip]
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _is_host_alive(ip: str, tcp_timeout: float = 0.5) -> bool:
    """ICMP ping first; TCP to common ports if host blocks ICMP."""
    if _ping_once(ip):
        return True
    for port in (80, 443, 22, 8080):
        try:
            with socket.create_connection((ip, port), timeout=tcp_timeout):
                return True
        except OSError:
            continue
    return False


def _resolve_hostname(ip: str) -> str | None:
    """Reverse DNS via OS resolver (often returns DHCP names from the router)."""
    try:
        name, _, _ = socket.gethostbyaddr(ip)
        if name and name != ip:
            return name
    except (socket.herror, socket.gaierror, OSError):
        pass
    return None


_META_TAG_RE = re.compile(r"<meta\b[^>]*>", re.IGNORECASE)
# Key=value pairs inside a meta tag (quoted values only)
_META_ATTR_RE = re.compile(r'([a-zA-Z][-a-zA-Z0-9_]*)\s*=\s*"([^"]*)"')
_META_ATTR_RE_SQ = re.compile(r"([a-zA-Z][-a-zA-Z0-9_]*)\s*=\s*'([^']*)'")


def _parse_meta_tag_attributes(tag: str) -> dict[str, str]:
    """Best-effort parse of meta tag attributes (double- or single-quoted values)."""
    attrs: dict[str, str] = {}
    for rx in (_META_ATTR_RE, _META_ATTR_RE_SQ):
        for m in rx.finditer(tag):
            attrs[m.group(1).lower()] = m.group(2)
    return attrs


def _find_meta_content(
    html: str,
    *,
    name: str | None = None,
    property_name: str | None = None,
) -> str | None:
    """Return trimmed content for meta name= or property= (e.g. og:site_name)."""
    want_name = (name or "").strip().lower()
    want_prop = (property_name or "").strip().lower()
    for m in _META_TAG_RE.finditer(html):
        attrs = _parse_meta_tag_attributes(m.group(0))
        content = (attrs.get("content") or "").strip()
        if not content:
            continue
        if want_name and attrs.get("name", "").lower() == want_name:
            return content
        if want_prop and attrs.get("property", "").lower() == want_prop:
            return content
    return None


_MAC_IN_ARP_LINE = re.compile(
    r"(?<![0-9A-Fa-f:])([0-9A-Fa-f]{1,2}(?::[0-9A-Fa-f]{1,2}){5})(?![0-9A-Fa-f:])",
    re.IGNORECASE,
)

# (lowercase substring in service banner, human-readable OS label)
_OS_SERVICE_HINTS: list[tuple[str, str]] = [
    ("microsoft windows", "Windows"),
    ("windows server", "Windows"),
    ("microsoft", "Windows"),
    ("windows", "Windows"),
    ("ubuntu", "Ubuntu"),
    ("debian", "Debian"),
    ("centos", "CentOS"),
    ("fedora", "Fedora"),
    ("alpine linux", "Alpine Linux"),
    ("alpine", "Alpine Linux"),
    ("red hat enterprise", "Red Hat Linux"),
    ("red hat", "Red Hat Linux"),
    ("rhel", "Red Hat Linux"),
    ("rocky linux", "Rocky Linux"),
    ("apple", "Apple / macOS"),
    ("macos", "Apple / macOS"),
    ("airport", "Apple AirPort"),
    ("freebsd", "FreeBSD"),
    ("netbsd", "NetBSD"),
    ("openbsd", "OpenBSD"),
    ("linux", "Linux"),
]


def _read_arp_cache(ip: str) -> str | None:
    """Resolve MAC from the kernel ARP cache after ping (same-L2 only)."""
    ip = str(ip).strip()
    if not ip:
        return None
    _ping_once(ip)

    try:
        proc = subprocess.run(
            ["arp", "-an"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout:
            for line in proc.stdout.splitlines():
                if ip not in line:
                    continue
                for m in _MAC_IN_ARP_LINE.finditer(line):
                    mac = _normalize_mac(m.group(1))
                    if mac and len(mac.replace(":", "")) == 12:
                        return mac
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.debug("arp -an not usable for %s: %s", ip, e)

    try:
        proc = subprocess.run(
            ["ip", "neigh", "show", ip],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout:
            for line in proc.stdout.splitlines():
                mm = re.search(r"lladdr\s+([0-9A-Fa-f:]+)", line, re.IGNORECASE)
                if mm:
                    mac = _normalize_mac(mm.group(1))
                    if mac and len(mac.replace(":", "")) == 12:
                        return mac
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.debug("ip neigh not usable for %s: %s", ip, e)

    return None


def _host_get(host: Any, key: str, default: Any = None) -> Any:
    if hasattr(host, "get"):
        return host.get(key, default)
    try:
        return host[key] if key in host else default
    except (TypeError, KeyError):
        return default


def _infer_os_from_services(host: Any) -> str | None:
    """Guess OS from nmap -sV product/version strings when OS fingerprinting is empty."""
    tcp = _host_get(host, "tcp") or {}
    if not tcp:
        return None
    parts: list[str] = []
    for pdata in tcp.values():
        if not isinstance(pdata, dict) or pdata.get("state") != "open":
            continue
        for k in ("product", "version", "extrainfo", "name"):
            v = pdata.get(k)
            if v:
                parts.append(str(v))
    text = " ".join(parts).lower()
    if not text.strip():
        return None
    for needle, label in _OS_SERVICE_HINTS:
        if needle in text:
            return label
    return None


def _finalize_discovery_host(row: dict[str, Any]) -> dict[str, Any] | None:
    """Drop nmap false positives without MAC; fill hostname from resolver when missing."""
    ip = row["ip"]
    has_mac = bool(row.get("mac"))
    if not has_mac and not _is_host_alive(ip):
        return None
    hostname = row.get("hostname")
    if not hostname:
        hostname = _resolve_hostname(ip)
    out = dict(row)
    out["hostname"] = hostname
    return out


class NetworkScanner:
    """Runs nmap and parses results; probes HTTP services for headers/title."""

    def __init__(self, port_scanner_class: type | None = None) -> None:
        self._port_scanner_class = port_scanner_class or nmap.PortScanner

    def discover_hosts(self, subnet: str) -> list[dict[str, Any]]:
        validate_subnet(subnet)
        nm = self._port_scanner_class()
        # -sn: host discovery; -PR ARP (needs NET_RAW on same L2); ping/TCP verify for no-MAC rows
        nm.scan(
            hosts=subnet.strip(),
            arguments="-sn -PR -PE -PS22,80,443,8080 -PA80 --max-retries 2 -T3",
        )
        candidates: list[dict[str, Any]] = []
        for host in nm.all_hosts():
            if nm[host].state() != "up":
                continue
            mac = None
            vendor = None
            hostname = None
            if "addresses" in nm[host]:
                addrs = nm[host]["addresses"]
                mac = _normalize_mac(addrs.get("mac"))
                if mac is None:
                    for k, v in addrs.items():
                        if k == "mac":
                            mac = _normalize_mac(v)
            if "vendor" in nm[host] and nm[host]["vendor"]:
                # nmap vendor dict: mac -> vendor name
                if mac and mac in nm[host]["vendor"]:
                    vendor = nm[host]["vendor"][mac]
                else:
                    vendor = next(iter(nm[host]["vendor"].values()), None)
            if "hostnames" in nm[host] and nm[host]["hostnames"]:
                hostname = nm[host]["hostnames"][0].get("name") or None
            candidates.append(
                {
                    "ip": host,
                    "mac": mac,
                    "hostname": hostname,
                    "vendor": vendor,
                }
            )
        with ThreadPoolExecutor(max_workers=32) as pool:
            finalized = list(pool.map(_finalize_discovery_host, candidates))
        return [row for row in finalized if row is not None]

    def scan_ports(self, target_ip: str, port_range: str = "1-1024") -> list[dict[str, Any]]:
        validate_target_ip(target_ip)
        nm = self._port_scanner_class()
        # -sT: TCP connect (works without raw sockets / caps in Docker)
        nm.scan(hosts=target_ip.strip(), arguments=f"-sT -T4 -p {port_range}")
        results: list[dict[str, Any]] = []
        if target_ip not in nm.all_hosts():
            return results
        host_data = nm[target_ip]
        if host_data.state() != "up":
            return results
        tcp = host_data.get("tcp") or {}
        for port, pdata in tcp.items():
            if pdata.get("state") != "open":
                continue
            results.append(
                {
                    "port": int(port),
                    "protocol": "tcp",
                    "state": pdata.get("state"),
                    "service_name": pdata.get("name"),
                    "service_version": (pdata.get("product") or "")
                    + (" " + pdata.get("version") if pdata.get("version") else ""),
                    "banner": pdata.get("extrainfo") or "",
                }
            )
        results.sort(key=lambda x: x["port"])
        return results

    def identify_host(self, target_ip: str) -> dict[str, Any]:
        """Best-effort hostname, MAC, and OS for a single IPv4 host via nmap."""
        validate_target_ip(target_ip)
        ip = target_ip.strip()
        hostname = _resolve_hostname(ip)
        mac_address: str | None = None
        os_guess: str | None = None

        _ping_once(ip)

        nm = self._port_scanner_class()
        full_args = "-O --osscan-guess -sV -T4 --host-timeout 50s"
        light_args = "-sV -T4 --host-timeout 50s"
        try:
            nm.scan(hosts=ip, arguments=full_args)
        except nmap.PortScannerError as e:
            logger.debug("identify_host: full nmap failed (%s), retrying without -O", e)
            try:
                nm.scan(hosts=ip, arguments=light_args)
            except nmap.PortScannerError as e2:
                logger.debug("identify_host: service-only nmap failed: %s", e2)

        if ip in nm.all_hosts():
            host = nm[ip]
            if host.state() == "up":
                addrs = host["addresses"] if "addresses" in host else None
                if isinstance(addrs, dict):
                    mac_address = _normalize_mac(addrs.get("mac"))
                    if mac_address is None:
                        for k, v in addrs.items():
                            if k == "mac":
                                mac_address = _normalize_mac(v)
                                break

                if not hostname:
                    hns = host["hostnames"] if "hostnames" in host else []
                    if hns:
                        first = hns[0]
                        nmap_name = first.get("name") if isinstance(first, dict) else None
                        if nmap_name and str(nmap_name).strip():
                            hostname = str(nmap_name).strip()

                osmatch = host["osmatch"] if "osmatch" in host else None
                if osmatch:
                    first_os = osmatch[0]
                    if isinstance(first_os, dict):
                        name = first_os.get("name")
                        if name and str(name).strip():
                            os_guess = str(name).strip()

        if mac_address is None:
            mac_address = _read_arp_cache(ip)

        if os_guess is None and ip in nm.all_hosts():
            host = nm[ip]
            if host.state() == "up":
                inferred = _infer_os_from_services(host)
                if inferred:
                    os_guess = inferred

        return {"hostname": hostname, "mac_address": mac_address, "os": os_guess}

    def probe_http_headers(self, ip: str, port: int, https: bool) -> dict[str, Any]:
        validate_target_ip(ip)
        scheme = "https" if https else "http"
        url = f"{scheme}://{ip}:{port}/"
        timeout = 4
        headers_out: dict[str, str] = {}
        title: str | None = None
        try:
            # GET is required for <title> and meta tags; HEAD has no body.
            resp = requests.get(url, timeout=timeout, verify=False, allow_redirects=True)
            for key in ("Server", "X-Powered-By"):
                if key in resp.headers:
                    headers_out[key] = resp.headers[key]
            # Parse body even on 4xx/5xx (some UIs still return HTML with a title)
            text = resp.text or ""
            m = re.search(r"<title[^>]*>([^<]{1,200})</title>", text, re.IGNORECASE | re.DOTALL)
            if m:
                title = re.sub(r"\s+", " ", m.group(1)).strip() or None
            application_name = _find_meta_content(text, name="application-name")
            og_site_name = _find_meta_content(text, property_name="og:site_name")
            generator = _find_meta_content(text, name="generator")
        except requests.RequestException as e:
            logger.debug("HTTP probe failed for %s: %s", url, e)
            return {
                "server": None,
                "x_powered_by": None,
                "title": None,
                "application_name": None,
                "og_site_name": None,
                "generator": None,
                "suggested_name": None,
                "error": str(e),
            }

        name_hint = (
            application_name
            or og_site_name
            or title
            or headers_out.get("Server")
        )
        return {
            "server": headers_out.get("Server"),
            "x_powered_by": headers_out.get("X-Powered-By"),
            "title": title,
            "application_name": application_name,
            "og_site_name": og_site_name,
            "generator": generator,
            "suggested_name": name_hint,
            "error": None,
        }

    def enrich_open_ports_with_http(
        self, target_ip: str, open_ports: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Add http_probe field to each open port (web ports only)."""
        enriched = []
        for row in open_ports:
            copy = dict(row)
            port = int(copy["port"])
            proto = (copy.get("service_name") or "").lower()
            is_https = port == 443 or port == 8443 or "https" in proto or "ssl" in proto
            is_httpish = port in _HTTP_LIKE_PORTS or "http" in proto or is_https
            if is_httpish:
                copy["https"] = bool(is_https)
                copy["http_probe"] = self.probe_http_headers(
                    target_ip, port, https=bool(is_https)
                )
            else:
                copy["https"] = False
                copy["http_probe"] = None
            enriched.append(copy)
        return enriched


# Silence urllib3 warnings for self-signed certs in homelab
try:
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass
