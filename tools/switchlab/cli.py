"""Command line entry point. Every command here is read-only."""

from __future__ import annotations

import argparse
import os
import sys

from switchlab.bridge.sysbotbase import BridgeError, SysBotBase, decode_result
from switchlab.identity import read_identity
from switchlab.regions import discover_regions, discover_regions_auto, scan_regions, scan_regions_kernel
from switchlab.scan import (OPS, CandidateCollapse, ScanSession, probe_widths, read_values,
                            refine, start_exact, start_exact_all_widths)
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
        if args.harvest:
            regions = discover_regions(client, max_probes=args.max_probes, depth=args.depth)
            scan = scan_regions(regions)
        else:
            regions = discover_regions_auto(client)
            scan = scan_regions_kernel(regions) if any(r.mem_type >= 0 for r in regions) else scan_regions(regions)
    if args.all:
        print("mapped regions:")
        for r in regions:
            print("  " + r.describe())
    print(f"scan set: {sum(r.size for r in scan) / 1024**2:.1f} MiB in {len(scan)} blocks")
    for r in scan[: args.show]:
        print("  " + r.describe())
    if len(scan) > args.show:
        print(f"  ... {len(scan) - args.show} more (use --show N)")
    return 0


def _require_lab(client: SysBotBase) -> None:
    if not client.is_lab():
        raise BridgeError("this command needs the sys-botbase-lab build on the Switch (getVersion should end in -lab)")


def cmd_scan(args: argparse.Namespace) -> int:
    with SysBotBase(_host(args), args.port, timeout=120) as client:
        ident = read_identity(client)
        if ident is None:
            raise BridgeError("no game is running")
        if args.scan_cmd == "probe":
            _require_lab(client)
            pairs = [(r.start, r.size) for r in scan_regions_kernel(discover_regions_auto(client, log=lambda *_: None))]
            print(f"counting matches for {args.value} across {sum(n for _, n in pairs) / 1024**2:.0f} MiB:")
            probe_widths(client, pairs, args.value, log=print)
            return 0
        if args.scan_cmd == "new":
            _require_lab(client)
            regions = scan_regions_kernel(discover_regions_auto(client, log=lambda *_: None))
            pairs = [(r.start, r.size) for r in regions]
            print(f"searching {sum(n for _, n in pairs) / 1024**2:.0f} MiB in {len(pairs)} regions on the Switch...")
            if args.width is None:
                sessions = start_exact_all_widths(client, pairs, args.value, args.label, ident.build_id, log=print)
                print(f"opened {len(sessions)} sessions: " + ", ".join(f"{args.label}-u{w*8}" for w in sessions))
                print("narrow every one of them; the wrong widths collapse and the right one survives")
                return 0
            session = start_exact(client, pairs, args.width, args.value, args.label, ident.build_id, log=print)
        elif args.scan_cmd == "next":
            session = ScanSession.load(ident.build_id, args.label)
            op = "exact" if args.value is not None else args.op
            if op is None:
                raise BridgeError("give --value N or one of --changed/--unchanged/--increased/--decreased")
            refine(client, session, op, args.value, log=print)
        elif args.scan_cmd == "show":
            session = ScanSession.load(ident.build_id, args.label)
            current = read_values(client, session.candidates[: args.limit], session.width)
            print(f"session {session.label}: {len(session.candidates)} candidates, width {session.width}")
            for a in session.candidates[: args.limit]:
                print(f"  0x{a:X}  now={current.get(a, '?')}  last={session.values.get(a, '?')}")
            for h in session.history[-5:]:
                print(f"  {h['time']} {h['op']} {h.get('value')}: {h['before']} -> {h['after']}")
            return 0
        else:
            raise BridgeError("unknown scan command")
    print(f"saved {session.path.relative_to(session.path.parents[2]) if session.path.is_relative_to(session.path.parents[2]) else session.path}")
    return 0


def cmd_files(args: argparse.Namespace) -> int:
    from pathlib import Path

    with SysBotBase(_host(args), args.port, timeout=60) as client:
        if args.files_cmd == "ls":
            for kind, size, name in client.fs_list(args.path):
                print(f"{kind} {size:>10}  {name}")
        elif args.files_cmd == "get":
            data = client.fs_get(args.remote)
            Path(args.local).write_bytes(data)
            print(f"got {args.remote} -> {args.local} ({len(data)} bytes)")
        elif args.files_cmd == "put":
            data = Path(args.local).read_bytes()
            client.fs_put_verified(args.remote, data)
            print(f"put {args.local} -> {args.remote} ({len(data)} bytes, verified by read-back)")
        elif args.files_cmd == "mkdir":
            client.fs_mkdir(args.path)
            print("ok")
        elif args.files_cmd == "rm":
            client.fs_delete(args.path)
            print("ok")
        elif args.files_cmd == "mv":
            client.fs_rename(args.src, args.dst)
            print("ok")
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
    s.add_argument("--harvest", action="store_true", help="force pointer harvesting even on the lab build")
    s.add_argument("--all", action="store_true", help="print every mapped region, not just the scan set")
    s.add_argument("--show", type=int, default=12, help="how many scan-set regions to print")
    s.set_defaults(func=cmd_regions)

    s = sub.add_parser("scan", help="candidate narrowing sessions (lab build)")
    ss = s.add_subparsers(dest="scan_cmd", required=True)
    b = ss.add_parser("probe", help="count matches per width before starting a session")
    b.add_argument("--value", type=int, required=True)
    n = ss.add_parser("new", help="on-device exact search into a new session")
    n.add_argument("--label", required=True)
    n.add_argument("--width", type=int, choices=[1, 2, 4, 8], default=None,
                   help="omit to open one session per usable width, which is the safe default")
    n.add_argument("--value", type=int, required=True)
    x = ss.add_parser("next", help="narrow an existing session by re-reading candidates")
    x.add_argument("--label", required=True)
    x.add_argument("--value", type=int, help="keep candidates equal to this value")
    g = x.add_mutually_exclusive_group()
    for op in OPS[1:]:
        g.add_argument(f"--{op}", dest="op", action="store_const", const=op)
    w = ss.add_parser("show", help="list candidates with current values")
    w.add_argument("--label", required=True)
    w.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_scan)

    s = sub.add_parser("files", help="SD card files through the lab2 build (paths like /switch/x.nro)")
    fs = s.add_subparsers(dest="files_cmd", required=True)
    a = fs.add_parser("ls"); a.add_argument("path")
    a = fs.add_parser("get"); a.add_argument("remote"); a.add_argument("local")
    a = fs.add_parser("put"); a.add_argument("local"); a.add_argument("remote")
    a = fs.add_parser("mkdir"); a.add_argument("path")
    a = fs.add_parser("rm"); a.add_argument("path")
    a = fs.add_parser("mv"); a.add_argument("src"); a.add_argument("dst")
    s.set_defaults(func=cmd_files)

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
    except CandidateCollapse as exc:
        print(f"search collapsed: {exc}", file=sys.stderr)
        return 3
    except BridgeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
