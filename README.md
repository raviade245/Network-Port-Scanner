# Network Port Scanner

A simple, personal-use TCP port scanner for your own network devices — available as both a **command-line tool** and a **desktop GUI**. Built with Python's standard library, so there's nothing extra to install for the core scanner.

> ⚠️ **Legal / Ethical Notice**
> Only scan devices and networks that you **own** or have **explicit permission** to test. Scanning networks or devices without authorization is illegal in most countries (including under India's IT Act, 2000). This tool is intended for personal use on your own home network, your own devices, or lab/practice environments you control.

---

## Features

- Scan a single IP, an entire subnet (CIDR notation, e.g. `192.168.1.0/24`), or a domain name (auto-resolved via DNS)
- Scan common ports by default, or specify a custom range/list
- Fast multi-threaded scanning
- Optional **banner grabbing** — pulls service/version info from open ports (SSH, FTP, SMTP, HTTP, etc.)
- Export results to **JSON** or **CSV**
- Two interfaces:
  - `port_scanner.py` — command-line
  - `port_scanner_gui.py` — desktop GUI (built with tkinter)

---

## Project Structure

```
.
├── scanner_core.py       # Shared scanning logic (used by both CLI and GUI)
├── port_scanner.py       # Command-line interface
├── port_scanner_gui.py   # Desktop GUI
├── requirements.txt
├── LICENSE
└── README.md
```

All three Python files must stay in the **same folder** — the CLI and GUI both import `scanner_core.py`.

---

## Requirements

- Python 3.7+
- `tkinter` (only needed for the GUI — included with most Python installs; on Debian/Kali-based systems install with `sudo apt install python3-tk`)

No third-party packages are required. See [`requirements.txt`](requirements.txt).

---

## Installation

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

That's it — no `pip install` needed for the core scanner.

---

## Usage

### Command-line

```bash
# Scan common ports on a single host
python3 port_scanner.py 192.168.1.1

# Scan a custom port range
python3 port_scanner.py 192.168.1.1 --ports 1-1000

# Scan specific ports
python3 port_scanner.py 192.168.1.1 --ports 21,22,80,443,3306

# Scan an entire subnet
python3 port_scanner.py 192.168.1.0/24

# Scan a domain name (resolved to its IP automatically)
python3 port_scanner.py example.com --ports 80,443

# Grab service banners on open ports
python3 port_scanner.py 192.168.1.1 --banner

# Export results
python3 port_scanner.py 192.168.1.1 --banner --export results.json
python3 port_scanner.py 192.168.1.1 --banner --export results.csv
```

**Options:**

| Flag | Description | Default |
|---|---|---|
| `target` | IP address, subnet (CIDR), or domain name | required |
| `--ports`, `-p` | Ports to scan (`1-1000` or `21,22,80`) | common ports |
| `--timeout`, `-t` | Socket timeout in seconds | `0.5` |
| `--workers`, `-w` | Max concurrent threads | `100` |
| `--banner`, `-b` | Enable banner grabbing | off |
| `--banner-timeout` | Timeout for banner grab attempts | `1.0` |
| `--export`, `-e` | Export path — `.csv` or `.json` | none |

### GUI

```bash
python3 port_scanner_gui.py
```

Enter a target IP/subnet, optional ports, toggle "Grab banners", and click **Start Scan**. Scans run in the background so the window stays responsive. Once finished, use **Export JSON** or **Export CSV** to save results.

---

## Roadmap / Ideas

- UDP port scanning
- Scheduled/recurring scans
- Scan history view in the GUI

---

## License

Released under the [MIT License](LICENSE).
