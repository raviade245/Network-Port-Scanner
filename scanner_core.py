"""
scanner_core.py
----------------
Shared scanning logic used by both the CLI (port_scanner.py) and the
GUI (port_scanner_gui.py). Keeping this in one place avoids duplicating
the scanning/banner-grabbing/export code in two tools.

Personal/authorized-use only. See port_scanner.py for the legal note.
"""

import socket
import csv
import json
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Common ports and their typical service names
COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt"
}


def parse_ports(port_str):
    """Parse a port string like '1-1000' or '21,22,80,443'."""
    ports = set()
    if not port_str:
        return sorted(COMMON_PORTS.keys())

    for part in port_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-")
            ports.update(range(int(start), int(end) + 1))
        else:
            ports.add(int(part))
    return sorted(ports)


def parse_targets(target_str):
    """Parse a target into a list of host addresses to scan.

    Accepts a plain IP, a CIDR subnet, or a domain name (resolved via DNS).
    Raises ValueError if the target is neither a valid IP/subnet nor a
    resolvable domain name.
    """
    try:
        network = ipaddress.ip_network(target_str, strict=False)
        if network.num_addresses > 1:
            return list(network.hosts())
        return [network.network_address]
    except ValueError:
        try:
            resolved_ip = socket.gethostbyname(target_str)
        except socket.gaierror:
            raise ValueError(
                target_str + " is not a valid IP/subnet and could not be resolved as a domain name"
            )
        return [ipaddress.ip_address(resolved_ip)]


def get_service_name(port):
    return COMMON_PORTS.get(port, "Unknown")


def scan_port(ip, port, timeout=0.5):
    """Attempt to connect to a single port. Returns port if open, else None."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((str(ip), port))
            if result == 0:
                return port
    except socket.error:
        pass
    return None


def grab_banner(ip, port, timeout=1.0):
    """Attempt to grab a service banner from an open port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((str(ip), port))

            if port in (80, 8080, 8000):
                sock.sendall(b"HEAD / HTTP/1.1\r\nHost: " + str(ip).encode() + b"\r\n\r\n")

            banner = sock.recv(1024)
            text = banner.decode(errors="ignore").strip()
            for line in text.splitlines():
                if line.strip():
                    return line.strip()[:120]
            return None
    except (socket.error, socket.timeout, OSError):
        return None


def scan_host(ip, ports, max_workers=100, grab_banners=False, banner_timeout=1.0,
              progress_callback=None):
    """Scan a single host across a list of ports using threads."""
    open_ports = []
    total = len(ports)
    done = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_port, ip, p): p for p in ports}
        for future in as_completed(futures):
            result = future.result()
            done += 1
            if progress_callback:
                progress_callback(done, total)
            if result:
                open_ports.append(result)
    open_ports.sort()

    if grab_banners and open_ports:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(grab_banner, ip, p, banner_timeout): p
                for p in open_ports
            }
            banners = {}
            for future in as_completed(futures):
                p = futures[future]
                banners[p] = future.result()
        return [(p, banners.get(p)) for p in open_ports]

    return [(p, None) for p in open_ports]


def scan_targets(target_str, port_str=None, max_workers=100, grab_banners=False,
                  timeout=0.5, banner_timeout=1.0, progress_callback=None):
    """High-level function: parses target(s) and ports, scans everything."""
    ports = parse_ports(port_str)
    hosts = parse_targets(target_str)

    result = {
        "scanned_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target": target_str,
        "hosts": []
    }

    for ip in hosts:
        open_ports = scan_host(ip, ports, max_workers, grab_banners, banner_timeout,
                                progress_callback)
        result["hosts"].append({
            "ip": str(ip),
            "open_ports": [
                {"port": p, "service": get_service_name(p), "banner": b}
                for p, b in open_ports
            ]
        })

    return result


def export_json(result, filepath):
    """Write a scan result dict to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(result, f, indent=2)


def export_csv(result, filepath):
    """Write a scan result dict to a CSV file (one row per open port)."""
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["scanned_at", "ip", "port", "service", "banner"])
        for host in result["hosts"]:
            if not host["open_ports"]:
                writer.writerow([result["scanned_at"], host["ip"], "", "no open ports found", ""])
                continue
            for entry in host["open_ports"]:
                writer.writerow([
                    result["scanned_at"], host["ip"], entry["port"],
                    entry["service"], entry["banner"] or ""
                ])
