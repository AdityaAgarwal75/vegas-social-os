"""Package one remote MCP plugin after the operator hosts a real endpoint."""
import argparse
import json
import urllib.parse
import zipfile
from pathlib import Path


def package(url, output):
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https" or not p.hostname or p.username or p.password or p.query or p.fragment or p.path != "/mcp":
        raise ValueError("Use an exact https://YOUR-ORIGIN/mcp endpoint without credentials/query")
    root = Path(__file__).resolve().parent.parent
    files = {"plugin.json": (root / "plugin.json").read_text(),
             "mcp.json": json.dumps({"$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
                 "mcpServers": {"vegas-social-os": {"type": "streamable-http", "url": url,
                     "extensions": {"com.openai": {"auth": {"type": "oauth", "client": {"mode": "dcr"}}}}}}}, indent=2)}
    # Skills reference the audited craft snapshots and product contracts. A
    # skills-only ZIP left those instructions/licenses dangling for new owners.
    for directory in ('skills', 'third_party'):
        for f in (root / directory).rglob('*'):
            if f.is_file(): files[f.relative_to(root).as_posix()] = f.read_text()
    for f in (root / 'docs').rglob('*'):
        if f.is_file() and f.suffix in ('.md', '.svg', '.png'):
            files[f.relative_to(root).as_posix()] = f.read_bytes()
    for name in ('BOOTSTRAP.md', 'AGENTS.md', 'README.md', 'agent-manifest.json'):
        files[name] = (root / name).read_text()
    output = Path(output).resolve()
    if root == output or root in output.parents:
        raise ValueError("Write the package outside the source checkout")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        for name, text in files.items(): z.writestr("vegas-social-os/" + name, text)
    return len(files)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    print("Packaged", package(args.url, args.output), "files. This does not deploy or publish the plugin.")
