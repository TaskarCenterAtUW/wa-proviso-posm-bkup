#!/usr/bin/env python3
"""Generate dataset boundary GeoJSON, search index, and PMTiles artifacts."""


""" THIS SCRIPT IS DEPRECATED. See the workflow file for details on the new approach using tippecanoe directly in the GitHub Actions workflow."""
# - the viewer now renders dataset boundaries from PMTiles instead of raw GeoJSON
# - search/popups still need lightweight dataset metadata and bounds without loading
#   full geometry into the browser
# - tippecanoe produces MBTiles first in this flow, so we explicitly convert that
#   output into a real PMTiles archive for the viewer/workflows to publish

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_INPUT_JSON = "tdei_datasets.json"
DEFAULT_OUTPUT_GEOJSON = "washington_dataset_boundaries.geojson"
DEFAULT_OUTPUT_INDEX = "washington_dataset_boundaries_index.json"
DEFAULT_OUTPUT_PMTILES = "washington_dataset_boundaries.pmtiles"
DEFAULT_LAYER_NAME = "wa-boundaries"


def scalarize(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return json.dumps(value, sort_keys=True)


def iter_positions(node):
    # Recursively walk nested Polygon/MultiPolygon coordinates so we can derive bounds
    # for each dataset boundary without adding a GIS dependency.
    if isinstance(node, list):
        if node and isinstance(node[0], (int, float)) and len(node) >= 2:
            yield node
            return
        for child in node:
            yield from iter_positions(child)


def compute_bbox(geometry):
    # Search in the viewer does not read boundary geometry from PMTiles. It reads the
    # precomputed bbox from the index JSON and uses that bbox for map.fitBounds(...).
    coords = list(iter_positions((geometry or {}).get("coordinates", [])))
    if not coords:
        return None
    lngs = [float(c[0]) for c in coords]
    lats = [float(c[1]) for c in coords]
    return {
        "minLng": min(lngs),
        "maxLng": max(lngs),
        "minLat": min(lats),
        "maxLat": max(lats),
    }


def feature_from_record(record):
    # Build two outputs from one dataset record:
    # 1. a full GeoJSON feature for PMTiles rendering
    # 2. a lightweight index entry for search/popup/fitBounds in the viewer
    geometry = record.get("geometry")
    if not geometry:
        return None, None

    bbox = compute_bbox(geometry)
    if not bbox:
        return None, None

    props = {}
    for key, value in record.items():
      if key in {"geometry", "custom_metadata"}:
        continue
      props[key] = scalarize(value)

    custom_metadata = record.get("custom_metadata") or {}
    if isinstance(custom_metadata, dict):
        for key, value in custom_metadata.items():
            props[key] = scalarize(value)

    feature = {
        "type": "Feature",
        "geometry": geometry,
        "properties": props,
    }
    # The viewer search uses bbox to zoom to matching datasets and center to anchor the
    # popup for the first match, without loading the full boundary GeoJSON in the page.
    center = {
        "lat": (bbox["minLat"] + bbox["maxLat"]) / 2,
        "lng": (bbox["minLng"] + bbox["maxLng"]) / 2,
    }
    index_item = {**props, "bbox": bbox, "center": center}
    return feature, index_item


def load_records(path: Path):
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}")
    return data


def write_json(path: Path, payload):
    path.write_text(json.dumps(payload, indent=2))


def build_geojson_and_index(records):
    # Produce both artifacts together so they stay in sync:
    # - GeoJSON feeds tippecanoe -> PMTiles for boundary rendering
    # - index JSON feeds name search + bbox-based fitBounds in the viewer
    features = []
    index = []
    for record in records:
        feature, index_item = feature_from_record(record)
        if feature is None:
            continue
        features.append(feature)
        index.append(index_item)

    if not features:
        raise ValueError("No boundary features found in input JSON")

    index.sort(key=lambda item: (item.get("name") or "").lower())
    return {"type": "FeatureCollection", "features": features}, index


def ensure_tool(name: str):
    tool = shutil.which(name)
    if not tool:
        raise FileNotFoundError(f"{name} is not installed or not on PATH")
    return tool


def run(command):
    print("Running:", " ".join(command))
    subprocess.run(command, check=True)


def build_pmtiles(geojson_path: Path, output_pmtiles: Path, layer_name: str, min_zoom: int, max_zoom: int):
    tippecanoe = ensure_tool("tippecanoe")
    pmtiles = ensure_tool("pmtiles")
    mbtiles_path = output_pmtiles.with_suffix(".mbtiles")
    ndjson_path = output_pmtiles.with_suffix(".ndjson")

    try:
        geojson = json.loads(geojson_path.read_text())
        with ndjson_path.open("w") as handle:
            for feature in geojson.get("features", []):
                handle.write(json.dumps(feature))
                handle.write("\n")

        run([
            tippecanoe,
            "--force",
            "--read-parallel",
            "--detect-shared-borders",
            "--no-feature-limit",
            "--no-tile-size-limit",
            "-Z",
            str(min_zoom),
            "-z",
            str(max_zoom),
            "-l",
            layer_name,
            "-o",
            str(mbtiles_path),
            str(ndjson_path),
        ])
        # Convert the intermediate MBTiles file into a real PMTiles archive.
        # The viewer renders boundaries from this PMTiles file, not from GeoJSON.
        if output_pmtiles.exists():
            output_pmtiles.unlink()
        run([pmtiles, "convert", str(mbtiles_path), str(output_pmtiles)])
        run([pmtiles, "verify", str(output_pmtiles)])
    finally:
        if mbtiles_path.exists():
            mbtiles_path.unlink()
        if ndjson_path.exists():
            ndjson_path.unlink()


def parse_args():
    parser = argparse.ArgumentParser(description="Generate TDEI dataset boundary PMTiles artifacts")
    parser.add_argument("--input-json", default=DEFAULT_INPUT_JSON)
    parser.add_argument("--output-geojson", default=DEFAULT_OUTPUT_GEOJSON)
    parser.add_argument("--output-index", default=DEFAULT_OUTPUT_INDEX)
    parser.add_argument("--output-pmtiles", default=DEFAULT_OUTPUT_PMTILES)
    parser.add_argument("--layer-name", default=DEFAULT_LAYER_NAME)
    parser.add_argument("--min-zoom", type=int, default=0)
    parser.add_argument("--max-zoom", type=int, default=16)
    parser.add_argument("--skip-pmtiles", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()

    input_json = Path(args.input_json)
    output_geojson = Path(args.output_geojson)
    output_index = Path(args.output_index)
    output_pmtiles = Path(args.output_pmtiles)

    records = load_records(input_json)
    geojson, index = build_geojson_and_index(records)
    write_json(output_geojson, geojson)
    write_json(output_index, index)
    print(f"Wrote {output_geojson} with {len(geojson['features'])} features")
    print(f"Wrote {output_index} with {len(index)} index items")

    if not args.skip_pmtiles:
        build_pmtiles(output_geojson, output_pmtiles, args.layer_name, args.min_zoom, args.max_zoom)
        print(f"Wrote {output_pmtiles}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
