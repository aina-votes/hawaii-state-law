"""Snapshot hawaii-law.db to DO Spaces — the durability leg of the three-copy
shape (laptop primary / bucket snapshots / droplet serving copy).

    python tools/snapshot.py           # backup -> gzip -> upload -> verify
    python tools/snapshot.py --list    # list existing snapshots

Run after every ingest. Each snapshot is a dated, content-hashed record of
"the law as we knew it" — conduct is judged under the law in force at the
time, so old snapshots are evidence, not clutter.

Credential model (reference_do_spaces_media): NO stored S3 keys. The vault
holds one dop_ control-plane token; this script mints an ephemeral
bucket-scoped S3 keypair, uploads PRIVATE (snapshots are not public objects,
unlike the media store), verifies, and deletes the keypair.
"""
import argparse
import gzip
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import urllib.request
from datetime import date

VAULT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(VAULT_DIR, "hawaii-law.db")
BUCKET = "fireflys-path-storage"
PREFIX = "hawaii-law/snapshots/"
REGIONS = ["sfo3", "sfo2", "nyc3", "ams3", "sgp1", "fra1", "syd1"]


def vault_token():
    env = dict(os.environ)
    env["PROTON_PASS_SESSION_DIR"] = os.path.expanduser("~/.proton-pass-agent/droplet")
    env["PROTON_PASS_AGENT_REASON"] = (
        "mint ephemeral Spaces key: hawaii-law.db snapshot (three-copy shape, "
        "decision 2026-07-26)")
    r = subprocess.run(["pass-cli", "item", "view",
                        "--vault-name", "Domain + Droplet Managment",
                        "--item-title", "DO_Object_Spaces_token",
                        "--output", "json"],
                       capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise RuntimeError("vault fetch failed: " + r.stderr.strip()[:200])
    d = json.loads(r.stdout)
    item = d.get("item", d)
    return next(f["content"]["Hidden"] for f in item["content"]["extra_fields"]
                if f.get("name") == "API Key")


def do_api(token, method, path, body=None):
    req = urllib.request.Request(
        "https://api.digitalocean.com" + path,
        data=json.dumps(body).encode() if body else None, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def s3_client(ak, sk):
    import boto3
    from botocore.client import Config
    for reg in REGIONS:
        s3 = boto3.client("s3", region_name=reg,
                          endpoint_url=f"https://{reg}.digitaloceanspaces.com",
                          aws_access_key_id=ak, aws_secret_access_key=sk,
                          config=Config(signature_version="s3v4"))
        try:
            s3.head_bucket(Bucket=BUCKET)
            return s3, reg
        except Exception:
            continue
    raise RuntimeError("bucket not found in any region")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    token = vault_token()
    print("token retrieved (in-process)")
    st, out = do_api(token, "POST", "/v2/spaces/keys",
                     {"name": "agent-ephemeral-hawaii-law-snapshot",
                      "grants": [{"bucket": BUCKET, "permission": "readwrite"}]})
    if st not in (200, 201):
        raise RuntimeError(f"key mint failed: {st} {json.dumps(out)[:300]}")
    key = out.get("key", out)
    ak, sk = key["access_key"], key["secret_key"]
    print("ephemeral key minted")
    try:
        s3, region = s3_client(ak, sk)
        if args.list:
            resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
            for o in resp.get("Contents", []):
                print(f"  {o['Key']}  {o['Size']/1e6:.1f}MB  {o['LastModified']}")
            print(f"{resp.get('KeyCount', 0)} snapshots")
            return

        if not os.path.exists(DB):
            raise RuntimeError("hawaii-law.db not found — build it first")
        # consistent copy via the sqlite backup API (safe against open writers)
        with tempfile.TemporaryDirectory() as td:
            snap = os.path.join(td, "snap.db")
            src = sqlite3.connect(DB)
            dst = sqlite3.connect(snap)
            src.backup(dst)
            dst.close()
            src.close()
            sha = hashlib.sha256(open(snap, "rb").read()).hexdigest()
            gz = snap + ".gz"
            with open(snap, "rb") as fi, gzip.open(gz, "wb") as fo:
                fo.writelines(fi)
            obj = f"{PREFIX}hawaii-law-{date.today().isoformat()}-{sha[:8]}.db.gz"
            size = os.path.getsize(gz)
            print(f"uploading {size/1e6:.1f}MB (sha256 {sha[:16]}…) -> {obj}")
            s3.upload_file(gz, BUCKET, obj,
                           ExtraArgs={"ContentType": "application/gzip",
                                      "Metadata": {"sha256": sha}})
            head = s3.head_object(Bucket=BUCKET, Key=obj)
            print("VERIFIED private object:", head["ContentLength"], "bytes,",
                  "sha256 meta:", head["Metadata"].get("sha256", "")[:16] + "…")
    finally:
        st2, _ = do_api(token, "DELETE", f"/v2/spaces/keys/{ak}")
        print("ephemeral key deleted:", st2)


if __name__ == "__main__":
    main()
