import argparse
import json
import os
import sys
from pathlib import Path

from .engine import Engine
from .store import Store
from .server import HTTPServer
from .tools import rpc


def main():
    parser = argparse.ArgumentParser(description="Vegas Social OS — self-hosted, ChatGPT-native content pipeline")
    parser.add_argument("command", choices=("serve", "stdio", "setup", "doctor", "flow-login", "call"))
    parser.add_argument("--data-dir", default=os.getenv("VSO_DATA_DIR", str(Path.home() / ".local/share/vegas-social-os")))
    parser.add_argument("--port", type=int, default=int(os.getenv("VSO_PORT", os.getenv("PORT", "8787"))))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--account-id")
    parser.add_argument("--name")
    parser.add_argument("--arguments", default="{}")
    args = parser.parse_args()
    base = os.getenv("VSO_PUBLIC_URL", "http://127.0.0.1:" + str(args.port)).rstrip("/")
    from urllib.parse import urlsplit
    p = urlsplit(base)
    if p.path or p.query or p.fragment or p.username or p.password or not p.hostname:
        parser.error("VSO_PUBLIC_URL must be an origin without path/query/userinfo")
    if p.scheme != "https" and not (p.scheme == "http" and p.hostname in ("127.0.0.1", "localhost")):
        parser.error("Use HTTPS except for loopback development")
    from .supabase_store import from_environment
    store = from_environment(args.data_dir)
    engine = Engine(store, base)
    if args.command == "setup":
        ticket = store.ticket("pair", {}, ttl=600)
        print("Private one-use setup link (expires in 10 minutes):")
        print(base + "/pair?ticket=" + ticket)
        print("Start the server with: python -m vso serve")
    elif args.command == "doctor": print(json.dumps(engine.doctor(), indent=2))
    elif args.command == "flow-login": print(json.dumps(engine.flow_login(args.account_id), indent=2))
    elif args.command == "call":
        from .tools import call
        print(json.dumps(call(engine, args.name, json.loads(args.arguments)), indent=2))
    elif args.command == "stdio":
        for line in sys.stdin:
            try:
                message = json.loads(line)
                result = rpc(engine, message)
            except Exception:
                result = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
            if result is not None: print(json.dumps(result), flush=True)
    else:
        from .recovery import startup
        startup(engine)
        server = HTTPServer((args.host, args.port), engine)
        print("Vegas Social OS listening at " + base + "; data stays outside the repository", file=sys.stderr)
        from .automation import start
        stop = start(engine)
        try: server.serve_forever()
        except KeyboardInterrupt: pass
        finally:
            stop.set()
            server.server_close()


if __name__ == "__main__": main()
