#!/usr/bin/env python3
"""Canonical entrypoint for the independent paper-parameter reproduction."""

from __future__ import annotations

import json

from run_paper_exact import parse_args, run


def main() -> int:
    summary = run(parse_args())
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["acceptance"]["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
