"""Import actual native-generated/edited bytes without echoing base64 to chat."""
import argparse
import base64
import json
import mimetypes
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vso.supabase_store import from_environment
from vso.engine import Engine

parser = argparse.ArgumentParser()
parser.add_argument("file", type=Path)
parser.add_argument("--data-dir", default=os.getenv("VSO_DATA_DIR", str(Path.home() / ".local/share/vegas-social-os")))
args = parser.parse_args()
if args.file.stat().st_size > 64 * 1024 * 1024: parser.error("Asset exceeds 64 MiB")
media_type = mimetypes.guess_type(args.file.name)[0]
result = Engine(from_environment(args.data_dir)).asset_import(base64.b64encode(args.file.read_bytes()).decode(), media_type)
print(json.dumps(result, indent=2))
