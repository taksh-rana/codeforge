"""
Upload this project to a NEW GitHub repo straight from your phone (Pydroid 3).
No git needed. Uses only the Python standard library.

1. Unzip CodeForge.zip somewhere (keep this file inside the CodeForge folder).
2. Make a GitHub token: GitHub > Settings > Developer settings >
   Personal access tokens > Tokens (classic) > Generate new token
   Tick the scopes:  repo  and  workflow
3. Run this file in Pydroid 3 and paste the token when asked.
"""
import base64, json, os, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {".git", ".gradle", "build", "__pycache__"}
SKIP_FILES = {"push_to_github.py"}
API = "https://api.github.com"


def call(method, path, token, body=None):
    req = urllib.request.Request(
        API + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={
            "Authorization": "token " + token,
            "Accept": "application/vnd.github+json",
            "User-Agent": "codeforge-push",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {}


def collect():
    files = []
    for root, dirs, names in os.walk(HERE):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for n in names:
            if n in SKIP_FILES:
                continue
            full = os.path.join(root, n)
            rel = os.path.relpath(full, HERE).replace(os.sep, "/")
            files.append((rel, full))
    # upload the workflow LAST so the build starts once, with everything present
    files.sort(key=lambda x: (x[0].startswith(".github/"), x[0]))
    return files


def main():
    token = input("Paste your GitHub token: ").strip()
    repo = input("New repo name [codeforge]: ").strip() or "codeforge"

    st, me = call("GET", "/user", token)
    if st != 200:
        sys.exit("Token rejected (HTTP %s). Check the token and its scopes." % st)
    owner = me["login"]
    print("Signed in as", owner)

    st, res = call("POST", "/user/repos", token,
                   {"name": repo, "private": False, "auto_init": True,
                    "description": "CodeForge - ad-free C/C++ compiler for Android"})
    if st == 422:
        print("Repo already exists, adding files to it.")
    elif st not in (200, 201):
        sys.exit("Could not create repo (HTTP %s): %s" % (st, res.get("message")))

    files = collect()
    for i, (rel, full) in enumerate(files, 1):
        with open(full, "rb") as fh:
            content = base64.b64encode(fh.read()).decode()
        body = {"message": "Add " + rel, "content": content}
        st, ex = call("GET", "/repos/%s/%s/contents/%s" % (owner, repo, rel), token)
        if st == 200 and "sha" in ex:
            body["sha"] = ex["sha"]
        st, res = call("PUT", "/repos/%s/%s/contents/%s" % (owner, repo, rel), token, body)
        if st not in (200, 201):
            sys.exit("Failed on %s (HTTP %s): %s" % (rel, st, res.get("message")))
        print("[%d/%d] %s" % (i, len(files), rel))

    print("\nDone! Open: https://github.com/%s/%s/actions" % (owner, repo))
    print("Wait for the green tick, open the run, and download 'CodeForge-APK' at the bottom.")


if __name__ == "__main__":
    main()
