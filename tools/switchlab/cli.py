"""Command line entry point. Every command here is read-only."""

from __future__ import annotations

import argparse
import os
import sys

from switchlab.bridge.sysbotbase import BridgeError, SysBotBase, decode_result
from switchlab.identity import read_identity
from switchlab.regions import discover_regions, scan_regions
from switchlab.screen import capture_screenshot


def _host(args: argparse.Namespace) -> str:
    host = args.host or os.environ.get("SWITCH_HOST", "")
    if not host:
        raise BridgeError("pass --host or set SWITCH_HOST (the Switch's LAN IP; never commit it)")
    return host


def cmd_status(args: argparse.Namespace) -> int:
    with SysBotBase(_host(args), args.port) as client:
        print(f"sys-botbase version: {client.get_version()}")
        ident = read_identity(client)
    if ident is None:
        print("No game is running (identity fields are empty).")
        return 1
    print(ident.describe())
    if ident.heap_base < 0x1000:
        print("warning: heap base looks invalid; another debugger probably holds the game. Run: switchlab diagnose")
        return 1
    return 0


def cmd_diagnose(args: argparse.Namespace) -> int:
    with SysBotBase(_host(args), args.port) as client:
        report = client.diagnose()
    for name, rc in report["codes"].items():
        print(f"{name:26} {rc} = {decode_result(rc)}")
    print(f"verdict: {report['verdict']}")
    return 0 if report["attached"] else 1


def cmd_regions(args: argparse.Namespace) -> int:
    with SysBotBase(_host(args), args.port, timeout=120) as client:
        regions = discover_regions(client, max_probes=args.max_probes, depth=args.depth)
    print("mapped regions:")
    for r in regions:
        print("  " + r.describe())
    scan = scan_regions(regions)
    print(f"scan set: {sum(r.size for r in scan) / 1024**2:.1f} MiB in {len(scan)} data blocks")
    return 0


def cmd_screenshot(args: argparse.Namespace) -> int:
    with SysBotBase(_host(args), args.port) as client:
        path = capture_screenshot(client, label=args.label)
    print(f"saved {path} ({path.stat().st_size} bytes)")
    return 0


def cmd_peek(args: argparse.Namespace) -> int:
    address = int(args.address, 0)
    with SysBotBase(_host(args), args.port) as client:
        if args.space == "main":
            data = client.peek_main(address, args.size)
        elif args.space == "heap":
            data = client.peek_heap(address, args.size)
        else:
            data = client.peek_absolute(address, args.size)
    for off in range(0, len(data), 16):
        chunk = data[off : off + 16]
        hexpart = " ".join(f"{b:02X}" for b in chunk)
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"{address + off:016X}  {hexpart:<47}  {text}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="switchlab", description="Read-only Switch research helper.")
    p.add_argument("--host", help="Switch LAN IP (or set SWITCH_HOST)")
    p.add_argument("--port", type=int, default=6000)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("status", help="show bridge version and the running game's identity")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("diagnose", help="explain why memory reads fail (kernel result codes)")
    s.set_defaults(func=cmd_diagnose)

    s = sub.add_parser("regions", help="discover mapped data regions by following pointers from the main module")
    s.add_argument("--max-probes", type=int, default=60)
    s.add_argument("--depth", type=int, default=2, help="pointer-following levels (1 = main module only)")
    s.set_defaults(func=cmd_regions)

    s = sub.add_parser("screenshot", help="save the current screen to local/screens/")
    s.add_argument("--label", default="screen")
    s.set_defaults(func=cmd_screenshot)

    s = sub.add_parser("peek", help="hex dump a small memory range (read-only)")
    s.add_argument("space", choices=["main", "heap", "abs"], help="address space")
    s.add_argument("address", help="offset or address, e.g. 0x1000")
    s.add_argument("size", type=int, help="bytes to read (keep small)")
    s.set_defaults(func=cmd_peek)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except BridgeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
