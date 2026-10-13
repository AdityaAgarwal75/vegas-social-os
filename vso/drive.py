"""Private Drive archive using app-created files only (drive.file scope).

An existing ChatGPT Drive connector does not transfer its tokens to this server.
The host can archive through its own authorized connector, or the operator can
connect Drive through this installation's official OAuth flow.
"""
import json
import uuid
from urllib.parse import quote

from . import net


def archive(engine, asset_id, account_id):
    account = engine.store.get("account", account_id)
    if account["provider"] != "drive" or account["status"] != "connected":
        raise ValueError("Connect an authorized Drive account first")
    asset = engine.store.get("asset", asset_id)
    file = engine.asset_path(asset_id)
    ident = engine.store.digest("drive:" + account_id + ":" + asset_id)[:32]
    with engine.store.db() as db:
        try: record = engine._load(db, "archive", ident)
        except ValueError: record = None
        if record:
            return record
        record = {"id": ident, "asset_id": asset_id, "account_id": account_id, "status": "uploading"}
        engine.store.write(db, "archive", ident, record)
    try:
        token = engine.accounts.token(account_id)
        metadata = {"name": file.name, "appProperties": {"vegasSocialAsset": asset_id}}
        boundary = "vso-" + uuid.uuid4().hex
        body = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" + json.dumps(metadata) +
                f"\r\n--{boundary}\r\nContent-Type: {asset['media_type']}\r\n\r\n").encode() + file.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
        result, _ = net.request("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink",
                                method="POST", token=token, raw=body, headers={"Content-Type": "multipart/related; boundary=" + boundary})
        record.update(status="archived", file_id=result["id"], url=result.get("webViewLink"))
    except Exception:
        record.update(status="unknown", error="Drive upload interrupted/rejected; reconcile the existing file before retrying")
    engine.store.put("archive", ident, record)
    return record


def reconcile(engine, archive_id):
    record = engine.store.get("archive", archive_id)
    token = engine.accounts.token(record["account_id"])
    query = "trashed = false and appProperties has { key='vegasSocialAsset' and value='" + record["asset_id"] + "' }"
    result, _ = net.request("https://www.googleapis.com/drive/v3/files?q=" + quote(query) + "&fields=files(id,name,webViewLink)&pageSize=10", token=token)
    files = result.get("files", [])
    if len(files) != 1:
        return {**record, "reconciliation": "No unique existing archive found; do not blindly resubmit", "matches": len(files)}
    record.update(status="archived", file_id=files[0]["id"], url=files[0].get("webViewLink"))
    engine.store.put("archive", archive_id, record)
    return record
