# -*- coding: utf-8 -*-
"""仅通过 api.github.com 发布本地快照（github.com 不可达时的备用通道）。

用法：
    GITHUB_TOKEN=<PAT> python assets/publish_api.py
或：
    echo <PAT> | python assets/publish_api.py

Token 只在内存中使用，不写入任何文件、不写入 git 配置。
"""
import os
import sys
import json
import base64
import subprocess
import urllib.request
import urllib.error

REPO = "moonquake2004/moto-dashboard"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.github.com"


def get_token():
    t = os.environ.get("GITHUB_TOKEN", "").strip()
    if t:
        return t
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def api(method, path, body=None, token=""):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "workbuddy-publish-api",
    })
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"message": raw[:300]}


def main():
    token = get_token()
    if not token:
        print("NO_TOKEN: 请通过 GITHUB_TOKEN 环境变量或 stdin 提供 PAT")
        return 1

    st, who = api("GET", "/user", token=token)
    if st != 200:
        print("TOKEN_INVALID:", st, who.get("message"))
        return 2
    print("AUTH_OK login=%s" % who.get("login"), flush=True)

    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    paths = [p for p in files.stdout.splitlines() if p.strip()]
    print("TRACKED_FILES: %d" % len(paths), flush=True)

    st, ref = api("GET", "/repos/%s/git/ref/heads/main" % REPO, token=token)
    if st != 200:
        print("GET_REF_FAILED:", st, ref.get("message"))
        return 3
    base_sha = ref["object"]["sha"]
    print("REMOTE_BASE: %s" % base_sha[:8], flush=True)

    tree = []
    for i, rel in enumerate(paths, 1):
        full = os.path.join(ROOT, rel)
        if not os.path.isfile(full):
            continue
        raw = open(full, "rb").read()
        st, blob = api("POST", "/repos/%s/git/blobs" % REPO, {
            "content": base64.b64encode(raw).decode(),
            "encoding": "base64",
        }, token)
        if st not in (201, 200) or not blob.get("sha"):
            print("BLOB_FAILED:", rel, st, blob.get("message"))
            return 4
        tree.append({"path": rel.replace("\\", "/"), "mode": "100644",
                     "type": "blob", "sha": blob["sha"]})
        if i % 15 == 0 or i == len(paths):
            print("  blob %d/%d" % (i, len(paths)), flush=True)

    st, new_tree = api("POST", "/repos/%s/git/trees" % REPO, {"tree": tree}, token)
    if st != 201 or not new_tree.get("sha"):
        print("TREE_FAILED:", st, new_tree.get("message"))
        return 5
    print("TREE_OK: %s" % new_tree["sha"][:8], flush=True)

    msg = "feat: 品牌型号补至439款/41张官方Logo；自建访问统计后端(Flask+SQLite)；修正RE未官方入华口径；删除hero副标题；changjiang Bobbie变体标uncertain"
    st, commit = api("POST", "/repos/%s/git/commits" % REPO, {
        "message": msg, "tree": new_tree["sha"], "parents": [base_sha],
        "author": {"name": "moonquake2004", "email": "moonquake2004@users.noreply.github.com"},
    }, token)
    if st != 201 or not commit.get("sha"):
        print("COMMIT_FAILED:", st, commit.get("message"))
        return 6

    st, ref2 = api("PATCH", "/repos/%s/git/refs/heads/main" % REPO,
                   {"sha": commit["sha"], "force": False}, token)
    if st != 200:
        print("UPDATE_REF_FAILED:", st, ref2.get("message"))
        return 7
    print("PUSH_OK head=%s | %s" % (commit["sha"][:8], msg), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
