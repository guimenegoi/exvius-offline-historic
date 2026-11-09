"""Render only the authentic pre-2.0 Global Home header/footer from original CPKs.

This is a transparent, static layout-validation preview, NOT a playable Home
screen, a 2016 launch APK, or an approved historical UI snapshot. No client
files or artwork are committed to the repository.

The original 640-pixel-wide CSV layouts are read directly from the signed
Global 1.2.0/1.4.1 APK. Coordinates and sprite frame rectangles are not
reconstructed from screenshots or guessed from the final Global 9.0.0 client.
"""
import argparse
import csv
import hashlib
import io
import json
import plistlib
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

from audit_historical_client_apks import CATALOGUE, audit

COMMON_CPK = "assets/cpk/common.cpk"
PRETUTORIAL_CPK = "assets/cpk/common_lang/sd/resources/resources_common_pretutorial.cpk"
ATLAS_DIRS = ("common", "header", "footer")
RESOLUTIONS = (960, 1024, 1136)
# A late-2024 CPK retains three obsolete craft button rows that resemble the
# 2016 Global UI. It is NOT the original Ver24_resources_common.cpk and its
# contents cannot be substituted for the missing 2016 localized asset pack.
LATE_ARCHIVE_COMMON_SHA256 = "ae6af108e2d7597b03b7b71b7b019558f06e6049dafc074de550b75dc43fb649"
LATE_CRAFT_LAYOUT_SHA256 = "bc91fd7617b96c8c8cb8ae578aede73acf2c1ab990ab921d69a076195145e06e"
LATE_CRAFT_LAYOUT_NAME = "layout/home/layout_home_craft.csv"


@dataclass(frozen=True)
class LayoutRow:
    x: int
    y: int
    width: int
    height: int
    font: int
    label: str
    sprite: str


def parse_layout(data: bytes) -> list[LayoutRow]:
    """Read original Cocos CSV geometry; retain its source order and signed x/y."""
    rows = []
    seen = set()
    for index, row in enumerate(csv.reader(io.StringIO(data.decode("utf-8-sig"))), 1):
        if not row or not any(row):
            continue
        if len(row) < 7:
            raise ValueError(f"Malformed layout row {index}: {row!r}")
        x, y, width, height, font = map(int, row[:5])
        label, sprite = row[5:7]
        if width <= 0 or height <= 0 or not label or label in seen:
            raise ValueError(f"Invalid or duplicate layout row {index}: {label}")
        seen.add(label)
        rows.append(LayoutRow(x, y, width, height, font, label, sprite))
    return rows


def inspect_preserved_craft_layout(archive_path: Path) -> dict:
    """Inspect legacy geometry retained in the later archive; never authenticate it as 2016.

    The coordinates are local to the craft panel, *not* global Home points.
    Sprite filenames are provenance clues, not proof that artwork is available.
    """
    if hashlib.sha256(archive_path.read_bytes()).hexdigest() != LATE_ARCHIVE_COMMON_SHA256:
        raise ValueError("Unrecognized late Global CPK; refusing layout attribution")
    from cricodecs import cpk
    archive = cpk.load(str(archive_path))
    infos = archive.file_infos()
    paths = {item.full_path: i for i, item in enumerate(infos)}
    if len(infos) != 1616 or len(paths) != len(infos):
        raise ValueError("Unexpected late Global CPK entry catalogue")
    csv_data = archive.file_bytes(paths[LATE_CRAFT_LAYOUT_NAME])
    if hashlib.sha256(csv_data).hexdigest() != LATE_CRAFT_LAYOUT_SHA256:
        raise ValueError("Late Global Home craft layout checksum mismatch")
    rows = parse_layout(csv_data)
    if len(rows) != 12:
        raise ValueError("Unexpected late Global craft control count")
    names = ("blacksmith", "ability", "prepare")
    buttons = [row for row in rows if row.label.startswith("home_btn_")]
    if [row.label for row in buttons] != [f"home_btn_{name}" for name in names]:
        raise ValueError("Unexpected late Global craft button order")
    if [(row.x, row.y, row.width, row.height) for row in buttons] != [
        (0, 0, 324, 128), (0, 144, 324, 128), (0, 288, 324, 128),
    ]:
        raise ValueError("Unexpected late Global legacy craft button geometry")
    expected = {
        f"home_{name}_icon_{suffix}" for name in names
        for suffix in ("bg", "gauge", "front")
    }
    if {row.label for row in rows if row not in buttons} != expected:
        raise ValueError("Unexpected late Global craft timer overlays")
    return {
        "type": "late-archive-surviving-legacy-layout-candidate",
        "source_pack_version": "Ver273_resources_common.cpk",
        "source_pack_year": 2024,
        "source_pack_sha256": LATE_ARCHIVE_COMMON_SHA256,
        "layout_path": LATE_CRAFT_LAYOUT_NAME,
        "layout_sha256": LATE_CRAFT_LAYOUT_SHA256,
        "original_2016_pack_matches": None,
        "original_2016_geometry_verified": False,
        "panel_origin_verified": False,
        "coordinate_system": "craft-panel-local",
        "original_english_artwork_recovered": False,
        "candidate_supported_by": [
            "GL 1.2.0 HomeScene::drawCraft(int) export",
            "May 22 2016 dated gameplay video, Home 00:10",
        ],
        "buttons": [
            {"name": row.label, "sprite": row.sprite,
             "rect": [row.x, row.y, row.width, row.height]}
            for row in buttons
        ],
        "timer_overlays": [
            {"name": row.label, "sprite": row.sprite,
             "rect": [row.x, row.y, row.width, row.height]}
            for row in rows if row not in buttons
        ],
    }


def frame_rectangle(metadata: dict) -> tuple[int, int, int, int]:
    """Accept the two original Cocos plist frame notations, without rotation."""
    if metadata.get("rotated", metadata.get("textureRotated", False)):
        raise ValueError("Rotated sprite atlas entry needs an explicit decoder")
    value = metadata.get("frame", metadata.get("textureRect"))
    if not isinstance(value, str):
        raise ValueError("Missing original sprite rectangle")
    parts = [int(n) for n in re.findall(r"-?\d+", value)]
    if len(parts) != 4 or parts[2] <= 0 or parts[3] <= 0:
        raise ValueError(f"Invalid sprite rectangle: {value}")
    return tuple(parts)


def render_common_shell(apk: Path, viewport_height: int, output: Path) -> dict:
    """Render backed-by-CPK header/footer; leave unavailable Home body transparent."""
    if viewport_height not in RESOLUTIONS:
        raise ValueError(f"Unsupported original 640px UI resolution: {viewport_height}")
    clients = json.loads(CATALOGUE.read_text(encoding="utf-8"))["client_builds"]
    matches = [r for r in clients if r["local_filename"] == apk.name]
    if len(matches) != 1 or matches[0]["version"] not in ("1.2.0", "1.4.1"):
        raise ValueError("Only verified, pre-2.0 Global signed APKs are supported")
    original = matches[0]
    # The existing project auditor already verifies APK SHA, signing metadata,
    # native evidence and embedded CPK presence; hashes for extracted assets
    # below are compared against its pinned catalogue before rendering.
    audit(apk, original)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite an existing preview: {output}")

    from PIL import Image
    from cricodecs import cpk

    expected = original["cpk_evidence"][0]
    assert expected["path"] == COMMON_CPK
    with ZipFile(apk) as z, tempfile.TemporaryDirectory(prefix="ffbe-pre2-shell-") as temp:
        packed = z.read(COMMON_CPK)
        if hashlib.sha256(packed).hexdigest() != expected["sha256"]:
            raise ValueError("Original UI package does not match the pinned CPK hash")
        archive_file = Path(temp) / "original.cpk"
        archive_file.write_bytes(packed)
        archive = cpk.load(str(archive_file))
        entries = archive.file_infos()
        if len(entries) != expected["entry_count"]:
            raise ValueError("Original CPK entry count differs")
        by_name = {entry.full_path: index for index, entry in enumerate(entries)}
        if len(by_name) != len(entries):
            raise ValueError("Duplicate paths in original CPK")
        def source(path: str) -> bytes:
            return archive.file_bytes(by_name[path])

        # The same signed APK has a second, incompatible pre-tutorial
        # header layout. Inspect and hash both rather than arbitrarily
        # choosing the other variant or overlaying its sprites on the Home.
        alternate_record = next(
            row for row in original["cpk_evidence"] if row["path"] == PRETUTORIAL_CPK
        )
        alternate_bytes = z.read(PRETUTORIAL_CPK)
        if hashlib.sha256(alternate_bytes).hexdigest() != alternate_record["sha256"]:
            raise ValueError("Original pre-tutorial CPK hash mismatch")
        alternate_file = Path(temp) / "pretutorial.cpk"
        alternate_file.write_bytes(alternate_bytes)
        alternate_archive = cpk.load(str(alternate_file))
        alternate_entries = alternate_archive.file_infos()
        if len(alternate_entries) != alternate_record["entry_count"]:
            raise ValueError("Original pre-tutorial CPK entry count changed")
        alternate_by_name = {row.full_path: i for i, row in enumerate(alternate_entries)}
        if len(alternate_by_name) != len(alternate_entries):
            raise ValueError("Duplicate pre-tutorial CPK paths")

        header_conflicts = []
        for name in ("layout/header/layout_header.csv",
                     f"layout/header/layout_header_640x{viewport_height}.csv"):
            candidate = alternate_archive.file_bytes(alternate_by_name[name])
            if hashlib.sha256(candidate).hexdigest() != alternate_record["asset_sha256"][name]:
                raise ValueError("Original pre-tutorial header layout checksum mismatch")
            common_rows = {row.label: row for row in parse_layout(source(name))}
            alternate_rows = {row.label: row for row in parse_layout(candidate)}
            if set(common_rows) != set(alternate_rows):
                raise ValueError("Header candidate control sets have changed")
            def geometry(row):
                return [row.x, row.y, row.width, row.height]
            differing = [
                {"control": label,
                 "common": geometry(common_rows[label]),
                 "pretutorial": geometry(alternate_rows[label])}
                for label in common_rows
                if common_rows[label] != alternate_rows[label]
            ]
            header_conflicts.append({"layout": name, "differences": differing})

        sprites = {}
        for group in ATLAS_DIRS:
            folder = f"image/ui/{group}/{group}"
            atlas_path = folder + ".png"
            plist_path = folder + ".plist"
            pixels = source(atlas_path)
            entries_metadata = source(plist_path)
            for file, blob in ((atlas_path, pixels), (plist_path, entries_metadata)):
                if hashlib.sha256(blob).hexdigest() != expected["asset_sha256"][file]:
                    raise ValueError(f"Original atlas hash mismatch: {file}")
            atlas = Image.open(io.BytesIO(pixels)).convert("RGBA")
            for name, metadata in plistlib.loads(entries_metadata)["frames"].items():
                if name in sprites:
                    raise ValueError(f"Ambiguous original sprite: {name}")
                sprites[name] = (atlas, metadata, group)

        layouts = (
            ("header", "layout/header/layout_header.csv"),
            ("footer", f"layout/footer/layout_footer_640x{viewport_height}.csv"),
        )
        canvas = Image.new("RGBA", (640, viewport_height), (0, 0, 0, 0))
        rendered = []
        for surface, layout_name in layouts:
            original_csv = source(layout_name)
            rows = parse_layout(original_csv)
            for row in rows:
                if not row.sprite:
                    continue  # Dynamic player labels are intentionally not fabricated.
                if row.sprite not in sprites:
                    raise ValueError(f"Missing original {surface} sprite: {row.sprite}")
                atlas, metadata, group = sprites[row.sprite]
                left, top, w, h = frame_rectangle(metadata)
                frame = atlas.crop((left, top, left + w, top + h))
                if frame.size != (row.width, row.height):
                    raise ValueError(f"{row.sprite}: actual sprite size and Cocos layout differ")
                # Negative positions occur in retail layout_footer_*.csv;
                # PIL paste clips them just as the viewport clips Cocos nodes.
                canvas.paste(frame, (row.x, row.y), frame)
                rendered.append({
                    "surface": surface,
                    "control": row.label,
                    "sprite": row.sprite,
                    "source_atlas": group,
                    "rect": [row.x, row.y, row.width, row.height],
                })
            if surface == "footer":
                footer_rows = [r for r in rows if r.label.startswith("footer_") and r.label != "footer_bg"]
                if [r.label for r in sorted(footer_rows, key=lambda r: r.x)] != [
                    "footer_home", "footer_unit", "footer_item",
                    "footer_shop", "footer_gacha", "footer_friend",
                ]:
                    raise ValueError("Unexpected authentic six-button footer layout")

        output.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output)
        return {
            "type": "historical-original-home-shell-only",
            "renderable": False,
            "layout_verified": False,
            "global_english_localization_verified": False,
            "embedded_art_locale_warning": (
                "Original APK-embedded header/footer sprites contain Japanese "
                "glyph labels; a dated Global English screenshot has English "
                "labels. Do not ship these sprites without recovered GL "
                "localization assets and runtime verification."
            ),
            "region": "GL",
            "source_version": original["version"],
            "original_apk_sha256": original["apk_sha256"],
            "original_common_cpk_sha256": expected["sha256"],
            "original_pretutorial_cpk_sha256": alternate_record["sha256"],
            "header_variant_used_for_static_preview": "common",
            "header_variant_selected_by_original_client": None,
            "header_variant_runtime_verified": False,
            "header_layout_candidate_comparison": header_conflicts,
            "viewport": [640, viewport_height],
            "surfaces": ["header", "footer"],
            "body": "transparent: original Home scene/layout not included in APK",
            "rendered_controls": rendered,
            "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--height", type=int, default=1024, choices=RESOLUTIONS)
    parser.add_argument("--late-common-cpk", type=Path,
                        help="Optional verified 2024 CPK to audit surviving craft rows; "
                             "never substitute its art for 2016")
    args = parser.parse_args()
    report = render_common_shell(args.apk, args.height, args.output)
    if args.late_common_cpk:
        report["legacy_craft_candidate"] = inspect_preserved_craft_layout(
            args.late_common_cpk)
    args.output.with_suffix(".json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "preview": str(args.output),
        "source_version": report["source_version"],
        "controls": len(report["rendered_controls"]),
        "sha256": report["output_sha256"],
        "layout_verified": False,
    }, indent=2))


if __name__ == "__main__":
    main()
