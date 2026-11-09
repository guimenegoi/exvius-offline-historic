"""Experimental preview APK packager for the existing 0.1.24 embedded runtime.

Requires .pyc files compiled by Python 3.10 (the original runtime's bytecode),
a Frida-compiled android_test.js bundle, and the upstream 0.1.24 APK.

Does NOT modify the existing upstream APK in place and does NOT sign the output.
Signing (v2/v3) and zip alignment are separate required steps before install.
The source's official reproducible build still needs original Global 9.0.0.
"""
from __future__ import annotations

from io import BytesIO
import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[2]
OLD_APK = ROOT / "release/exvius-offline-v0.1.24.apk"
REPLACED = {
    "player_state.pyc": "source/server/player_state.py",
    "offline_menu.pyc": "source/server/offline_menu.py",
    "ffbe_gacha.pyc": "source/server/ffbe_gacha.py",
    "android_game.pyc": "source/memorial/android/src/main/python/android_game.py",
    "event_archive.pyc": "source/server/event_archive.py",
    "ffbe_player.pyc": "source/server/ffbe_player.py",
    "exvius_actions.pyc": "source/server/exvius_actions.py",
    "exvius_colosseum.pyc": "source/server/exvius_colosseum.py",
    "exvius_actions_shops.pyc": "source/server/exvius_actions_shops.py",
    "ffbe_friends.pyc": "source/server/ffbe_friends.py",
    "gacha_archive.pyc": "source/server/gacha_archive.py",
    "capture_server.pyc": "source/server/capture_server.py",
}
ADDED = {
    "historical_progression.pyc": "source/server/historical_progression.py",
    "historical_summons.pyc": "source/server/historical_summons.py",
    "historical_preview_data.pyc": "source/server/historical_preview_data.py",
    "historical_login_preview.pyc": "source/server/historical_login_preview.py",
}
EXPECTED_MAGIC = bytes.fromhex("6f0d0d0a")  # Python 3.10 Chaquopy runtime


def zip_with_replacements(raw: bytes, replacements: dict[str, bytes]) -> bytes:
    output = BytesIO()
    with ZipFile(BytesIO(raw)) as archive, ZipFile(output, "w") as dest:
        found = set()
        for info in archive.infolist():
            name = info.filename
            if name in replacements:
                found.add(name)
            dest.writestr(info, replacements.get(name, archive.read(name)))
        for name, value in replacements.items():
            if name not in found:
                dest.writestr(name, value, compress_type=ZIP_DEFLATED)
    return output.getvalue()


def script_body(path: Path) -> bytes:
    raw = path.read_bytes()
    tokens = (b"function ", b"(", b"!", b"var ", b"let ", b"const ",
              b"Object.defineProperty", b'"use strict"', b"'use strict'", b"//", b"/*")
    lines = raw.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.lstrip().startswith(tokens):
            body = b"".join(lines[i:])
            if b"frida-java-bridge" in body:
                raise ValueError("Unexpected injection of duplicate Java bridge.")
            return body
    raise ValueError("Frida compiled bundle contains no executable JavaScript.")


def update_manifest_version_code(manifest: bytes, next_code: int) -> tuple[bytes, int]:
    """Patch only android:versionCode in the already-installed package's AXML.

    The original bytecode-host APK stores versionCode as TYPE_INT_DEC. Preserve
    every other binary-manifest byte, especially the application/package name.
    """
    if len(manifest) < 8 or struct.unpack_from("<H", manifest)[0] != 0x0003:
        raise ValueError("Not a binary Android XML manifest.")
    if not 0 < next_code < 2 ** 31:
        raise ValueError("Invalid Android version code.")
    offset, names = 8, None
    candidate = None
    while offset + 8 <= len(manifest):
        kind, header, length = struct.unpack_from("<HHI", manifest, offset)
        if length < header or length < 8 or offset + length > len(manifest):
            raise ValueError("Invalid Android XML chunk.")
        if kind == 0x0180:
            names = [struct.unpack_from("<I", manifest, i)[0]
                     for i in range(offset + header, offset + length, 4)]
        if kind == 0x0102 and names is not None:
            start, width, count = struct.unpack_from("<HHH", manifest, offset + 24)
            if width != 20:
                raise ValueError("Unexpected Android XML attribute width.")
            for i in range(count):
                attribute = offset + 16 + start + i * width
                if attribute + width > offset + length:
                    raise ValueError("Truncated Android manifest attribute.")
                name = struct.unpack_from("<I", manifest, attribute + 4)[0]
                if name < len(names) and names[name] == 0x0101021b:
                    if manifest[attribute + 15] != 0x10 or candidate is not None:
                        raise ValueError("Unsupported or repeated Android version code.")
                    candidate = attribute + 16
            break
        offset += length
    if candidate is None:
        raise ValueError("Android manifest versionCode was not found.")
    previous = struct.unpack_from("<I", manifest, candidate)[0]
    if next_code <= previous:
        raise ValueError("Updatable APK needs a versionCode greater than its base.")
    revised = bytearray(manifest)
    struct.pack_into("<I", revised, candidate, next_code)
    return bytes(revised), previous


def package(base: Path, compiled: Path, js: Path, destination: Path, version_code: int | None = None) -> dict:
    files = {**REPLACED, **ADDED}
    updates = {}
    for archive_name, source in files.items():
        pyc = compiled / archive_name
        if not pyc.is_file():
            raise FileNotFoundError(f"Missing Python 3.10 compiled bytecode: {pyc}")
        blob = pyc.read_bytes()
        if blob[:4] != EXPECTED_MAGIC:
            raise ValueError(f"Wrong Python bytecode version: {pyc}")
        updates[archive_name] = blob
    assert len(updates) == len(files)

    with ZipFile(base) as original:
        original_members = set(original.namelist())
        archive_file = "assets/chaquopy/app.imy"
        frida_script = "lib/arm64-v8a/libexviustest.js.so"
        if not {archive_file, frida_script} <= original_members:
            raise ValueError("Not the expected Chaquopy + Frida 0.1.24 APK.")
        pyarchive = original.read(archive_file)
        with ZipFile(BytesIO(pyarchive)) as check:
            if check.read("player_state.pyc")[:4] != EXPECTED_MAGIC:
                raise ValueError("Base APK does not embed the expected Python 3.10 runtime.")
        archive_blob = zip_with_replacements(pyarchive, updates)
        replacements = {archive_file: archive_blob, frida_script: script_body(js)}
        previous_code = None
        if version_code is not None:
            replacements["AndroidManifest.xml"], previous_code = update_manifest_version_code(
                original.read("AndroidManifest.xml"), version_code)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(destination, "w") as output:
            for info in original.infolist():
                member = info.filename
                # Do not carry stale v1 signatures to a new, unsigned archive.
                if member.startswith("META-INF/") and member.upper().endswith((".RSA", ".DSA", ".EC", ".SF", "/MANIFEST.MF")):
                    continue
                output.writestr(info, replacements.get(member, original.read(member)))
    with ZipFile(destination) as result:
        with ZipFile(BytesIO(result.read(archive_file))) as inner:
            for member, expected in updates.items():
                if inner.read(member) != expected:
                    raise RuntimeError(f"Python overlay missing: {member}")
        if result.read(frida_script) != replacements[frida_script]:
            raise RuntimeError("Title menu JavaScript overlay missing.")
    return {
        "base_apk_sha256": hashlib.sha256(base.read_bytes()).hexdigest(),
        "unsigned_apk_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "preview_index_sha256": hashlib.sha256((ROOT / "source/server/historical_preview_data.py").read_bytes()).hexdigest(),
        "python_modules": sorted(updates),
        "android_base_version_code": previous_code,
        "android_updated_version_code": version_code,
        "script_bytes": len(replacements[frida_script]),
        "signing": "REQUIRED, not an installable APK until signed",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=OLD_APK)
    parser.add_argument("--compiled", type=Path, default=ROOT / "source/build/historical-preview/pyc")
    parser.add_argument("--js", type=Path, default=ROOT / "source/build/historical-preview/android_test.bundle.js")
    parser.add_argument("--output", type=Path, default=ROOT / "source/build/historical-preview/historic-preview-unsigned.apk")
    parser.add_argument("--version-code", type=int, help="Upgrade code (must exceed base APK).")
    args = parser.parse_args()
    print(json.dumps(package(args.base, args.compiled, args.js, args.output,
                             version_code=args.version_code), indent=2))


if __name__ == "__main__":
    main()
