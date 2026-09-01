from __future__ import annotations

import argparse
import os
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="open-ux", description="Open UX server")
    parser.add_argument(
        "mode",
        nargs="?",
        choices=("stdio", "http", "validate-catalog"),
        default=os.environ.get("OPEN_UX_MODE", "stdio"),
    )
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", os.environ.get("OPEN_UX_PORT", "8080"))),
    )
    args = parser.parse_args(argv)

    if args.mode == "validate-catalog":
        from open_ux.catalog import load_catalog

        catalog = load_catalog()
        print(
            f"catalog ok version={catalog.version} "
            f"guidelines={len(catalog.guidelines)} bytes={catalog.size_bytes}"
        )
        return 0

    if args.mode == "stdio":
        from open_ux.server import create_mcp

        create_mcp(hosted=False).run(transport="stdio")
        return 0

    from open_ux.http_app import serve_http

    serve_http(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
