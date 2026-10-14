"""Owner-chosen dashboard password. Password does NOT replace MCP OAuth/PKCE."""
import hashlib
import hmac
import json
import secrets
import time


def configured(store):
    try: return bool(store.get("owner-auth", "password").get("hash"))
    except ValueError: return False


def password_set(store, password):
    if not isinstance(password, str) or len(password)<14 or len(password)>256:
        raise ValueError("Choose a private password of 14-256 characters")
    salt=secrets.token_bytes(16)
    hashed=hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1,dklen=32)
    with store.db() as db:
        store.write(db,"owner-auth","password",{"algorithm":"scrypt-n16384-r8-p1",
            "salt":salt.hex(),"hash":hashed.hex(),"updated_at":time.time()})
        db.execute("DELETE FROM records WHERE kind='session'")
    return {"configured":True,"sessions_revoked":True}


def password_check(store, value, remote):
    if not configured(store): raise ValueError("Owner password is not configured")
    from .auth import rate_limit
    rate_limit(store,"password-global","owner",15,900)
    rate_limit(store,"password-peer",remote,7,900)
    record=store.get("owner-auth","password")
    salt=bytes.fromhex(record["salt"])
    digest=hashlib.scrypt((value if isinstance(value,str) else "").encode(),
        salt=salt,n=2**14,r=8,p=1,dklen=32)
    try:valid=hmac.compare_digest(digest,bytes.fromhex(record["hash"]))
    except (ValueError,KeyError):valid=False
    return valid


def validate_return(value):
    if not isinstance(value,str) or len(value)>3000:
        raise ValueError("Invalid local destination")
    if value=="/dashboard":return value
    if value.startswith("/authorize?") and all(x not in value for x in ("\r","\n","\\","#")):
        return value
    raise ValueError("Local login destination must be /dashboard or a local OAuth authorize request")
