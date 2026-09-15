#!/usr/bin/env python3
"""
Simple Network Port Scanner (CLI)
-----------------------------------
Personal-use tool to scan devices on YOUR OWN network for open TCP ports.

⚠️ IMPORTANT / LEGAL NOTE:
Only scan devices and networks that you own or have explicit permission
to test. Scanning networks/devices without authorization is illegal in
most countries (including under India's IT Act, 2000). Use this only on
your home network, personal devices, or lab environments you control.

Usage examples:
    python3 port_scanner.py 192.168.1.1
    python3 port_scanner.py 192.168.1.1 --ports 1-1000
    python3 port_scanner.py 192.168.1.1 --ports 21,22,80,443,3306
    python3 port_scanner.py 192.168.1.0/24 --banner
    python3 port_scanner.py 192.168.1.1 --export results.json
    python3 port_scanner.py 192.168.1.1 --export results.csv

Requires scanner_core.py to be in the same folder.
"""

import argparse
import sys
import os

import scanner_core as core


def main():
    parser = argparse.ArgumentParser(
        description="Simple TCP Port Scanner (for personal/authorized use only)"
    )
    parser.add_argument("target", help="Target IP address or subnet (e.g. 192.168.1.1 or 192.168.1.0/24)")
    parser.add_argument("--ports", "-p", help="Ports to scan (e.g. '1-1000' or '21,22,80'). Default: common ports")
    parser.add_argument("--timeout", "-t", type=float, default=0.5, help="Socket timeout in seconds (default 0.5)")
    parser.add_argument("--workers", "-w", type=int, default=100, help="Max concurrent threads (default 100)")
    parser.add_argument("--banner", "-b", action="store_true", help="Attempt banner grabbing on open ports")
    parser.add_argument("--banner-timeout", type=float, default=1.0, help="Timeout for banner grab attempts (default 1.0)")
    parser.add_argument("--export", "-e", help="Export results to a file. Extension decides format: .csv or .json")

    args = parser.parse_args()

    try:
        result = core.scan_targets(
            args.target,
            port_str=args.ports,
            max_workers=args.workers,
            grab_banners=args.banner,
            timeout=args.timeout,
            banner_timeout=args.banner_timeout,
        )
    except ValueError:
        print(f"[!] Invalid IP/subnet: {args.target}")
        sys.exit(1)

    total_ports = len(core.parse_ports(args.ports))
    print("=" * 55)
    print(f" Port Scanner started at {result['scanned_at']}")
    print(f" Target(s): {args.target}  |  Ports: {total_ports}  |  Hosts: {len(result['hosts'])}")
    print("=" * 55)

    for host in result["hosts"]:
        print(f"\n[+] Scanning host: {host['ip']}")
        if host["open_ports"]:
            print(f"    Open ports on {host['ip']}:")
            for entry in host["open_ports"]:
                line = f"      {entry['port']}/tcp\tOPEN\t{entry['service']}"
                if args.banner:
                    line += f"\t| {entry['banner'] if entry['banner'] else 'no banner received'}"
                print(line)
        else:
            print(f"    No open ports found on {host['ip']} (in scanned range).")

    print("\n" + "=" * 55)
    print(" Scan complete.")
    print("=" * 55)

    if args.export:
        ext = os.path.splitext(args.export)[1].lower()
        if ext == ".json":
            core.export_json(result, args.export)
        elif ext == ".csv":
            core.export_csv(result, args.export)
        else:
            print(f"[!] Unknown export extension '{ext}'. Use .csv or .json")
            sys.exit(1)
        print(f"[+] Results exported to {args.export}")


if __name__ == "__main__":
    main()
