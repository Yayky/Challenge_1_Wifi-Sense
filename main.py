#!/usr/bin/env python3
"""WiFi Sense – detect presence, count people, and classify activity using WiFi CSI."""

import argparse
from server import serve


def main() -> None:
    p = argparse.ArgumentParser(
        description="WiFi Sense — real-time presence detection via WiFi CSI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # simulation (no hardware needed)
  python main.py --mode esp32             # receive data from ESP32 over UDP
  python main.py --mode esp32 --port 8080 --udp-port 5000
        """,
    )
    p.add_argument(
        "--mode",
        choices=["simulate", "esp32"],
        default="simulate",
        help="Data source: simulate (default) or esp32",
    )
    p.add_argument("--host", default="0.0.0.0", help="HTTP host (default: 0.0.0.0)")
    p.add_argument("--port", type=int, default=8000, help="HTTP port (default: 8000)")
    p.add_argument("--udp-host", default="0.0.0.0", help="UDP listen host (esp32 mode)")
    p.add_argument("--udp-port", type=int, default=5000, help="UDP listen port (esp32 mode)")

    args = p.parse_args()
    serve(
        mode=args.mode,
        host=args.host,
        port=args.port,
        udp_host=args.udp_host,
        udp_port=args.udp_port,
    )


if __name__ == "__main__":
    main()
