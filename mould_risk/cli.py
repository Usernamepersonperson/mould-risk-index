"""Command line: demo, fetch, advise, decode."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import weather
from .advice import Reading, advise, surface_rh_of
from .sensors import PayloadError, decode_payload

ROOT = Path(__file__).resolve().parent.parent


def cmd_demo(args) -> int:
    from .figures import make_figures
    from .study import run_all

    out = Path(args.out)
    res = run_all(out, quick=args.quick)
    if not args.no_figures:
        make_figures(res, out)
    print((out / "results.md").read_text(encoding="utf-8"))
    print(f"written to {out}")
    return 0


def cmd_fetch(_args) -> int:
    print(json.dumps(weather.fetch_all(), indent=1))
    return 0


def cmd_advise(args) -> int:
    r = Reading(args.t_in, args.rh_in, args.t_out, args.rh_out, args.frsi, args.mould_index, args.hours_over_80)
    print(f"wall surface RH at the monitored spot: {surface_rh_of(r):.0f} %")
    for a in advise(r):
        print(f"[{a.severity}] {a.text(args.lang)}")
    return 0


def cmd_decode(args) -> int:
    try:
        print(json.dumps(decode_payload(bytes.fromhex(args.hex)), indent=1))
    except (PayloadError, ValueError) as e:
        print(f"error: {e}")
        return 1
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="mould_risk", description="Open-source mould and condensation risk monitor")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo", help="run all experiments, write results and figures")
    d.add_argument("--out", default=str(ROOT / "docs"))
    d.add_argument("--quick", action="store_true", help="2 cities instead of 6 (CI)")
    d.add_argument("--no-figures", action="store_true")
    d.set_defaults(fn=cmd_demo)
    f = sub.add_parser("fetch", help="download outdoor weather again (Open-Meteo)")
    f.set_defaults(fn=cmd_fetch)
    a = sub.add_parser("advise", help="advice for one reading")
    a.add_argument("--t-in", type=float, required=True)
    a.add_argument("--rh-in", type=float, required=True)
    a.add_argument("--t-out", type=float, required=True)
    a.add_argument("--rh-out", type=float, required=True)
    a.add_argument("--frsi", type=float, default=0.70)
    a.add_argument("--mould-index", type=float, default=0.0)
    a.add_argument("--hours-over-80", type=int, default=0)
    a.add_argument("--lang", choices=["de", "fr", "it", "en"], default="en")
    a.set_defaults(fn=cmd_advise)
    c = sub.add_parser("decode", help="decode a 7-byte sensor payload (hex)")
    c.add_argument("hex")
    c.set_defaults(fn=cmd_decode)
    args = p.parse_args(argv)
    return args.fn(args)
