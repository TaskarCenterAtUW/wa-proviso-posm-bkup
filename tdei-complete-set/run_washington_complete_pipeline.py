#!/usr/bin/env python3
"""Run end-to-end dataset pipeline for Washington complete PMTiles generation."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
import json
from pathlib import Path

from fetch_all_projects import TDEIDatasetDownloader


FULL_DATASET_ID = "cbbe1150-25a1-40f7-9965-49b50ea0efc6"
BOUNDARIES_GEOJSON = "washington_dataset_boundaries.geojson"
OUTPUT_PMTILES = "washington_complete.pmtiles"
LAYER_NAME = "wa-proviso-data"
BOUNDARIES_INDEX_JSON = "washington_dataset_boundaries_index.json"
BOUNDARIES_PMTILES = "washington_dataset_boundaries.pmtiles"
TDEI_USERNAME = "<>"
TDEI_PASSWORD = "<>"


def run_cmd(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    print(f"[RUN] {' '.join(command)}")
    subprocess.run(command, cwd=cwd, check=True, env=env)


def run_shell(command: str, cwd: Path) -> None:
    print(f"[RUN] {command}")
    subprocess.run(command, cwd=cwd, check=True, shell=True, executable="/bin/zsh")


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required tool not found on PATH: {name}")


def extract_zip(zip_path: Path, extract_dir: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)
    print(f"[INFO] Extracted {zip_path} -> {extract_dir}")


def extract_nested_zips(root_dir: Path) -> None:
    for path in root_dir.rglob("*.zip"):
        nested_extract_dir = path.with_suffix("")
        extract_zip(path, nested_extract_dir)


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    downloads_dir = script_dir / "downloads"

    require_tool("jq")
    require_tool("tippecanoe")
    require_tool("python3")

    # 1) call fetch_all_projects.py in default mode so it fetches published datasets
    # and produces tdei_datasets.json used for boundaries generation.
    # Inject hardcoded credentials because fetch_all_projects.py reads from env vars.
    child_env = os.environ.copy()
    child_env["TDEI_USERNAME"] = TDEI_USERNAME
    child_env["TDEI_PASSWORD"] = TDEI_PASSWORD
    run_cmd(["python3", "fetch_all_projects.py"], cwd=script_dir, env=child_env)
    datasets_json_path = script_dir / "tdei_datasets.json"
    if not datasets_json_path.exists():
        raise RuntimeError(f"Expected datasets file was not created: {datasets_json_path}")
    with datasets_json_path.open("r", encoding="utf-8") as handle:
        published_datasets = json.load(handle)
    print(f"[INFO] Published datasets found: {len(published_datasets)}")
    for item in published_datasets:
        dataset_id = item.get("tdei_dataset_id")
        dataset_name = item.get("name", "")
        if dataset_id:
            print(f"[PUBLISHED] {dataset_id} | {dataset_name}")

    # 2) call extract_downloaded_projects.py
    run_cmd(["python3", "extract_downloaded_projects.py"], cwd=script_dir)

    # 3) generate boundaries geojson from tdei_datasets.json
    jq_cmd = (
        "jq '{type: \"FeatureCollection\",features: map({type: \"Feature\",geometry: .geometry,"
        "properties: (del(.geometry) | .custom_metadata as $custom | del(.custom_metadata) | . + $custom)})}' "
        "tdei_datasets.json > washington_dataset_boundaries.geojson"
    )
    run_shell(jq_cmd, cwd=script_dir)
    boundaries_path = script_dir / BOUNDARIES_GEOJSON
    if not boundaries_path.exists():
        raise RuntimeError(f"Failed to create boundaries file: {boundaries_path}")

    # 4) download full dataset with hardcoded dataset id
    downloader = TDEIDatasetDownloader()
    downloader.get_access_token(TDEI_USERNAME, TDEI_PASSWORD)
    downloader.download_dataset(FULL_DATASET_ID, download_folder=str(downloads_dir))

    # Extract top-level and nested zip for this full dataset only
    full_dataset_zip = downloads_dir / f"{FULL_DATASET_ID}.zip"
    if not full_dataset_zip.exists():
        raise RuntimeError(f"Dataset zip not found: {full_dataset_zip}")
    full_dataset_extract_dir = downloads_dir / FULL_DATASET_ID
    extract_zip(full_dataset_zip, full_dataset_extract_dir)
    extract_nested_zips(full_dataset_extract_dir)

    # 5) build complete PMTiles using only boundaries + full dataset geojson files
    pmtiles_input_dir = downloads_dir / "_pmtiles_input"
    if pmtiles_input_dir.exists():
        shutil.rmtree(pmtiles_input_dir)
    pmtiles_input_dir.mkdir(parents=True, exist_ok=True)

    staged_boundaries = pmtiles_input_dir / BOUNDARIES_GEOJSON
    shutil.copy2(boundaries_path, staged_boundaries)

    copied_geojson_count = 0
    for geojson_path in full_dataset_extract_dir.rglob("*.geojson"):
        relative_part = geojson_path.relative_to(full_dataset_extract_dir)
        destination = pmtiles_input_dir / "full_dataset" / relative_part
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(geojson_path, destination)
        copied_geojson_count += 1

    if copied_geojson_count == 0:
        raise RuntimeError(f"No .geojson files found under {full_dataset_extract_dir}")

    tippecanoe_cmd = (
        "find ./downloads/_pmtiles_input -name \"*.geojson\" -exec jq -c '.features[]' {} + "
        f"| tippecanoe -z 18 -Z 8 -o {OUTPUT_PMTILES} "
        f"--drop-densest-as-needed --extend-zooms-if-still-dropping -l {LAYER_NAME}"
    )
    run_shell(tippecanoe_cmd, cwd=script_dir)

    # 6) generate boundary index file (same as workflow)
    run_cmd(["python3", "generate_boundary_index.py"], cwd=script_dir)
    boundaries_index_path = script_dir / BOUNDARIES_INDEX_JSON
    if not boundaries_index_path.exists():
        raise RuntimeError(f"Boundary index output not created: {boundaries_index_path}")

    # 7) generate boundary-only PMTiles (same as workflow)
    boundary_pmtiles_cmd = (
        f"jq -c '.features[]' {BOUNDARIES_GEOJSON} > washington_dataset_boundaries.ndjson\n"
        "tippecanoe "
        "--force "
        "--read-parallel "
        "--detect-shared-borders "
        "--no-feature-limit "
        "--no-tile-size-limit "
        "-Z 0 -z 16 "
        "-l wa-boundaries "
        f"-o {BOUNDARIES_PMTILES} "
        "washington_dataset_boundaries.ndjson\n"
        "rm -f washington_dataset_boundaries.ndjson"
    )
    run_shell(boundary_pmtiles_cmd, cwd=script_dir)
    boundary_pmtiles_path = script_dir / BOUNDARIES_PMTILES
    if not boundary_pmtiles_path.exists():
        raise RuntimeError(f"Boundary PMTiles output not created: {boundary_pmtiles_path}")

    output_pmtiles_path = script_dir / OUTPUT_PMTILES
    if not output_pmtiles_path.exists():
        raise RuntimeError(f"PMTiles output not created: {output_pmtiles_path}")

    print(f"[DONE] Created {output_pmtiles_path}")
    print(f"[INFO] Included: boundaries + {copied_geojson_count} geojson file(s) from {FULL_DATASET_ID}")
    print(f"[DONE] Created {boundaries_index_path}")
    print(f"[DONE] Created {boundary_pmtiles_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1)
