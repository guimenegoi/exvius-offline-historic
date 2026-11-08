"""Fetch individual original Global master tables by HTTP byte range.

Reads the official data-001 ZIP's central directory remotely: no 1.2 GB ZIP
download. Validates individual ZIP entry CRCs; this is NOT a full-pack SHA test.
Only the named, audited files are allowed to be extracted locally.

    python3 source/exvius/fetch_historical_tables.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
from urllib.request import Request, urlopen
import zlib

ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "static/mst_decoded/F_UNIT_MST.ndjson",
    "static/text_decoded/F_TEXT_UNITS_NAME.ndjson",
)
MAX_RANGE = 16 * 1024 * 1024


def http_range(url: str, start: int, end: int) -> bytes:
    amount = end - start + 1
    if start < 0 or amount <= 0 or amount > MAX_RANGE:
        raise ValueError("Range exceeds safe download size.")
    request = Request(url, headers={"Range": f"bytes={start}-{end}"})
    with urlopen(request, timeout=45) as response:
        payload = response.read(MAX_RANGE + 1)
        if (response.status != 206 or len(payload) != amount or
                not response.headers.get("Content-Range", "").startswith(f"bytes {start}-{end}/")):
            raise RuntimeError("Host did not honor the requested ZIP byte range.")
        return payload


def central_directory(total: int, read_range) -> dict:
    """Return ZIP central entries with documented, safe offsets and sizes."""
    tail_start = max(0, total - 131072)
    tail = read_range(tail_start, total - 1)
    position = tail.rfind(b"PK\x05\x06")
    if position < 0 or len(tail) - position < 22:
        raise ValueError("ZIP end-of-central-directory record not found.")
    record = struct.unpack_from("<4s4H2LH", tail, position)
    _, disk, cd_disk, on_disk, count, size, offset, comment = record
    if (disk or cd_disk or on_disk != count or count == 0xffff or
            size == 0xffffffff or offset == 0xffffffff or
            position + 22 + comment > len(tail) or size > MAX_RANGE):
        raise ValueError("Unsupported multi-volume or ZIP64 central directory.")
    directory = read_range(offset, offset + size - 1)
    pointer, result = 0, {}
    for _ in range(count):
        if pointer + 46 > len(directory):
            raise ValueError("Truncated ZIP central directory.")
        fields = struct.unpack_from("<4s6H3L5H2L", directory, pointer)
        if fields[0] != b"PK\x01\x02":
            raise ValueError("Invalid ZIP central directory signature.")
        name_len, extra_len, comment_len = fields[10:13]
        name = directory[pointer + 46:pointer + 46 + name_len].decode("utf-8")
        result[name] = {
            "crc": fields[7], "compressed_size": fields[8],
            "size": fields[9], "method": fields[4], "offset": fields[-1],
        }
        pointer += 46 + name_len + extra_len + comment_len
    if pointer != size:
        raise ValueError("ZIP central directory length mismatch.")
    return result


def extract_entry(entry: dict, read_range) -> bytes:
    """Fetch exactly one compressed file, checking its metadata and CRC."""
    offset = entry["offset"]
    local = read_range(offset, offset + 29)
    fields = struct.unpack("<4s5H3L2H", local)
    if fields[0] != b"PK\x03\x04" or fields[3] != entry["method"]:
        raise ValueError("ZIP local header does not match central directory.")
    start = offset + 30 + fields[9] + fields[10]
    if entry["compressed_size"] > MAX_RANGE:
        raise ValueError("Table exceeds range cap; do not download entire ZIP.")
    compressed = read_range(start, start + entry["compressed_size"] - 1)
    if entry["method"] == 8:
        content = zlib.decompress(compressed, -zlib.MAX_WBITS)
    elif entry["method"] == 0:
        content = compressed
    else:
        raise ValueError("Unsupported ZIP compression method.")
    if len(content) != entry["size"] or (zlib.crc32(content) & 0xffffffff) != entry["crc"]:
        raise ValueError("ZIP entry failed size or CRC validation.")
    return content


def fetch_selected(manifest: dict, root: Path, read_range_factory=http_range) -> dict:
    pack = next((p for p in manifest["packs"] if p["id"] == "data-001"), None)
    if not pack:
        raise ValueError("No data-001 pack in the official manifest.")
    url, size = pack["url"], int(pack["size"])
    read_range = lambda a, b: read_range_factory(url, a, b)
    entries = central_directory(size, read_range)
    verified = {}
    for name in FILES:
        entry = entries.get(name)
        if entry is None:
            raise ValueError(f"Required original master table absent: {name}")
        relative = Path(name.removeprefix("static/"))
        destination = root / relative
        if destination.is_file():
            content = destination.read_bytes()
            if len(content) == entry["size"] and zlib.crc32(content) & 0xffffffff == entry["crc"]:
                verified[name] = {"path": str(destination), "size": len(content), "reused": True}
                continue
        content = extract_entry(entry, read_range)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = destination.with_suffix(destination.suffix + ".tmp")
        temp.write_bytes(content)
        temp.replace(destination)
        verified[name] = {"path": str(destination), "size": len(content), "reused": False}
    return verified


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/latest.json")
    parser.add_argument("--output-root", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    outcome = fetch_selected(json.loads(args.manifest.read_text("utf-8")), args.output_root)
    for name, item in outcome.items():
        print(f"{name}: {item['size']} bytes -> {item['path']}"
              + (" (already verified)" if item["reused"] else " (downloaded and CRC-verified)"))


if __name__ == "__main__":
    main()
