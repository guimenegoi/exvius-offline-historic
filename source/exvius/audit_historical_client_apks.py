"""Verify archived FFBE Global clients without modifying APKs or shipping their bytes.

This is native binary evidence for UI eras, not a UI implementation.
Requires the standard Unix nm and c++filt tools; optional keytool.
"""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = ROOT / "source/server/content/historical_ui_snapshots.json"
CLASSES = ("HomeScene", "GateScene", "HomeRotateMenuList")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def native_features(library: bytes) -> dict:
    """Count actual exported C++ methods, preserving multiple ctor overloads."""
    with tempfile.TemporaryDirectory(prefix="ffbe-historic-symbols-") as directory:
        elf = Path(directory) / "libgame.so"
        elf.write_bytes(library)
        symbols = subprocess.run(
            ["nm", "-D", "--defined-only", str(elf)],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines()
    mangled = [line.split()[-1] for line in symbols if line.strip()]
    names = subprocess.run(
        ["c++filt"], input="\n".join(mangled),
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    if len(names) != len(mangled):
        raise ValueError("Native demangling changed the exported symbol count.")
    classes = {
        name: [sym for sym in names if sym.startswith(name + "::")]
        for name in CLASSES
    }
    return {
        "export_count": len(mangled),
        "scene_export_counts": {name: len(matches) for name, matches in classes.items()},
        "home_draw_craft": "HomeScene::drawCraft(int)" in classes["HomeScene"],
        "home_rotate_menu_list": bool(classes["HomeRotateMenuList"]),
        "home_rotate_colosseum_orbs": any(
            sym.startswith("HomeRotateMenuList::setClsmOrb(")
            for sym in classes["HomeRotateMenuList"]
        ),
        "gate_list_layout": any(
            sym.startswith("GateScene::setListLayout(") for sym in classes["GateScene"]
        ),
    }


def certificate_sha1(apk: Path, keytool: str) -> str:
    raw = subprocess.run(
        [keytool, "-printcert", "-jarfile", str(apk)],
        capture_output=True, text=True, check=True,
    ).stdout
    match = re.search(r"\bSHA1:\s*((?:[0-9a-fA-F]{2}:){19}[0-9a-fA-F]{2})", raw)
    if not match:
        raise ValueError("No v1 certificate SHA-1 in keytool output.")
    return match.group(1).replace(":", "").lower()


def audit(apk: Path, record: dict, keytool: str | None = None,
          verify_cpk: bool = False) -> dict:
    """Fail closed on package-byte, signature, native or scene mismatches."""
    if not apk.is_file():
        raise FileNotFoundError(apk)
    actual_hash = hashlib.sha256()
    with apk.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            actual_hash.update(chunk)
    if actual_hash.hexdigest() != record["apk_sha256"]:
        raise ValueError(f"{apk.name}: APK checksum mismatch")
    with ZipFile(apk) as package:
        if package.testzip() is not None:
            raise ValueError(f"{apk.name}: corrupted ZIP entry")
        library = package.read("lib/x86/libgame.so")
        bundled = "assets/cpk/common.cpk" in package.namelist()
        if verify_cpk:
            # Reuse the project's existing CriCodecs loader and only inspect
            # pinned, read-only original assets from authenticated APK bytes.
            import plistlib
            from cricodecs import cpk

            with tempfile.TemporaryDirectory(prefix="ffbe-original-cpk-") as folder:
                for number, expected in enumerate(record["cpk_evidence"]):
                    content = package.read(expected["path"])
                    if digest(content) != expected["sha256"]:
                        raise ValueError(f"{apk.name}: CPK checksum mismatch")
                    file = Path(folder) / f"{number}.cpk"
                    file.write_bytes(content)
                    archive = cpk.load(str(file))
                    entries = archive.file_infos()
                    if len(entries) != expected["entry_count"]:
                        raise ValueError(f"{apk.name}: unexpected CPK entry count")
                    named = {item.full_path: position
                             for position, item in enumerate(entries)}
                    if len(named) != len(entries):
                        raise ValueError(f"{apk.name}: duplicate original CPK paths")
                    for name, reference in expected["asset_sha256"].items():
                        actual = archive.file_bytes(named[name])
                        if digest(actual) != reference:
                            raise ValueError(f"{apk.name}: original asset checksum mismatch: {name}")
                    for name, count in expected.get("sprite_frame_counts", {}).items():
                        atlas = plistlib.loads(archive.file_bytes(named[name]))
                        if len(atlas["frames"]) != count:
                            raise ValueError(f"{apk.name}: original sprite count changed: {name}")
    if digest(library) != record["x86_libgame_sha256"]:
        raise ValueError(f"{apk.name}: libgame.so checksum mismatch")
    actual = native_features(library)
    for key in ("scene_export_counts", "home_draw_craft",
                "home_rotate_menu_list", "home_rotate_colosseum_orbs",
                "gate_list_layout"):
        if actual[key] != record["native_evidence"][key]:
            raise ValueError(f"{apk.name}: unexpected native evidence: {key}")
    if bundled != record["bundled_common_cpk"]:
        raise ValueError(f"{apk.name}: bundled CPK status changed")
    if keytool and certificate_sha1(apk, keytool) != record["signing_cert_sha1"]:
        raise ValueError(f"{apk.name}: unexpected signing certificate")
    return {
        "version": record["version"],
        "apk_sha256": record["apk_sha256"],
        "x86_libgame_sha256": record["x86_libgame_sha256"],
        "native_evidence": actual,
        "bundled_common_cpk": bundled,
        "signature_checked": bool(keytool),
        "cpk_evidence_verified": verify_cpk,
        "historical_ui_layout_approved": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path,
                        help="Local folder with APKs, never copied into Git")
    parser.add_argument("--keytool", help="JDK keytool executable to verify APK signer")
    parser.add_argument("--catalogue", type=Path, default=CATALOGUE)
    parser.add_argument("--verify-cpk", action="store_true",
                        help="Verify original assets with the existing CriCodecs decoder")
    args = parser.parse_args()
    records = json.loads(args.catalogue.read_text(encoding="utf-8"))["client_builds"]
    report = [audit(args.directory / row["local_filename"], row,
                    args.keytool, args.verify_cpk) for row in records]
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
