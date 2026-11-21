# -*- coding: utf-8 -*-
"""仅通过 api.github.com 发布本地快照（github.com 不可达时的备用通道）。

用法：
    GITHUB_TOKEN=<PAT> COMMIT_MSG="feat: ..." python assets/publish_api.py
或：
    echo <PAT> | python assets/publish_api.py

Token 只在内存中使用，不写入任何文件、不写入 git 配置。

注意：本脚本是「用本地文件整棵替换远端树」，本地不存在的远端文件会被删掉。
默认会在删除前中止，确认要删请加 ALLOW_DELETE=1。
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

    # 推的是工作区文件，不是某个 commit：有未提交改动时中止，避免把半成品发上去
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if dirty and os.environ.get("ALLOW_DIRTY", "") != "1":
        print("ABORT: 工作区有未提交改动（确认要连同这些改动一起发布请设 ALLOW_DIRTY=1）：")
        print("\n".join("   " + l for l in dirty.splitlines()[:20]))
        return 10

    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    paths = [p for p in files.stdout.splitlines() if p.strip()]
    print("TRACKED_FILES: %d" % len(paths), flush=True)

    st, ref = api("GET", "/repos/%s/git/ref/heads/main" % REPO, token=token)
    if st != 200:
        print("GET_REF_FAILED:", st, ref.get("message"))
        return 3
    base_sha = ref["object"]["sha"]
    print("REMOTE_BASE: %s" % base_sha[:8], flush=True)

    # 整树替换前先确认不会误删远端独有的文件
    st, remote = api("GET", "/repos/%s/git/trees/%s?recursive=1" % (REPO, base_sha), token=token)
    # 拿不到远端树就无法判断会不会误删，必须中止，而不是跳过检查继续推
    if st != 200:
        print("GET_TREE_FAILED:", st, remote.get("message"))
        return 9
    if remote.get("truncated"):
        print("ABORT: 远端树过大被截断，无法完整比对删除清单")
        return 9
    remote_modes = {t["path"]: t.get("mode") for t in remote.get("tree", []) if t.get("type") == "blob"}
    if True:
        remote_paths = set(remote_modes)
        missing = sorted(remote_paths - set(paths))
        if missing and os.environ.get("ALLOW_DELETE", "") != "1":
            print("ABORT: 本地缺少以下远端文件，整树替换会把它们删掉（确认删除请设 ALLOW_DELETE=1）：")
            for m in missing[:20]:
                print("   -", m)
            print("   ... 共 %d 个" % len(missing))
            return 8

    tree = []
    for i, rel in enumerate(paths, 1):
        full = os.path.join(ROOT, rel)
        if not os.path.isfile(full):
            continue
        with open(full, "rb") as fh:
            raw = fh.read()
        # 保留可执行位：本地有 x 位或远端原来就是 100755，都按 100755 提交
        mode = "100755" if (os.stat(full).st_mode & 0o111 or remote_modes.get(rel) == "100755") else "100644"
        st, blob = api("POST", "/repos/%s/git/blobs" % REPO, {
            "content": base64.b64encode(raw).decode(),
            "encoding": "base64",
        }, token)
        if st not in (201, 200) or not blob.get("sha"):
            print("BLOB_FAILED:", rel, st, blob.get("message"))
            return 4
        tree.append({"path": rel.replace("\\", "/"), "mode": mode,
                     "type": "blob", "sha": blob["sha"]})
        if i % 15 == 0 or i == len(paths):
            print("  blob %d/%d" % (i, len(paths)), flush=True)

    st, new_tree = api("POST", "/repos/%s/git/trees" % REPO, {"tree": tree}, token)
    if st != 201 or not new_tree.get("sha"):
        print("TREE_FAILED:", st, new_tree.get("message"))
        return 5
    print("TREE_OK: %s" % new_tree["sha"][:8], flush=True)

    msg = os.environ.get("COMMIT_MSG") or "chore: sync dashboard snapshot"
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
