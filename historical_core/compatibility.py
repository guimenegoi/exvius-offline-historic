"""Read-only source/API and APK fingerprint comparison between offline releases.

No automatic migration or declaration of binary compatibility.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

WATCH = (
    "source/server/", "source/exvius/", "source/memorial/",
    "source/docs/", "release/app.json", "release/notes-",
)


def git_lines(repo, *args):
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True
    ).splitlines()


def compare_sources(repo, baseline, candidate):
    # Only compare fully specified Git refs, no checkout, fetch, or mutation.
    changes = git_lines(repo, "diff", "--name-status", baseline, candidate, "--")
    details = []
    for line in changes:
        parts = line.split("\t")
        name = parts[-1]
        if name.startswith("source/server/") or name.startswith("source/exvius/") or name.startswith("source/memorial/"):
            category = "runtime_source"
        elif name.startswith("release/"):
            category = "release_metadata"
        elif name.startswith("source/docs/"):
            category = "documentation"
        else:
            category = "other"
        details.append({"change": parts[0], "path": name, "category": category})
    return {
        "baseline": git_lines(repo, "rev-parse", baseline)[0],
        "candidate": git_lines(repo, "rev-parse", candidate)[0],
        "changes": details,
        "runtime_changed": any(x["category"] == "runtime_source" for x in details),
        "binary_engine_compatibility": "not_established",
    }


def apk_fingerprint(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    with zipfile.ZipFile(path) as apk:
        names = apk.namelist()
        def category(prefix):
            return sorted(n for n in names if n.startswith(prefix))
        native = category("lib/")
        rules = category("assets/rules/")
        chaquopy = category("assets/chaquopy/")
        return {
            "filename": path.name,
            "sha256": digest.hexdigest(),
            "bytes": path.stat().st_size,
            "native_libraries": native,
            "rules_asset_count": len(rules),
            "rules_assets_sha256": hashlib.sha256(
                "\n".join(rules).encode("utf-8")
            ).hexdigest(),
            "chaquopy_asset_count": len(chaquopy),
            "binary_engine_compatibility": "not_established",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--baseline", default="upstream/main")
    parser.add_argument("--candidate", default="HEAD")
    parser.add_argument("--apk", help="optional local APK to fingerprint, never uploaded")
    args = parser.parse_args()
    report = {"source": compare_sources(args.repo, args.baseline, args.candidate)}
    if args.apk:
        report["apk"] = apk_fingerprint(args.apk)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
