# wa-proviso-posm-bkup
Function app that takes backup of POSM DB and uploads to storage container

# Workflow
- Workflow contains the code to dump the data from POSTGRESQL and then upload to blob storage.
TODO:
- Make it a cron job
- Keep a latest version always
- Make pbf using planet-dump
- extract geojson using osmium
- Convert to .pmtiles using tippecanoe

## TDEI Datasets backup

Command to consolidate all the metadat features

 jq '{"type": "FeatureCollection", "features": [.[] |  .dataset_detail.dataset_area.features[]]}' --slurp ./downloads/*/metadata.json > washington_dataset_boundaries.geojson

 jq '{"type": "FeatureCollection", "features": [.[] | .dataset_detail as $detail |  .dataset_detail.dataset_area.features[] | .properties.dataset_name = $detail.name | .properties.dataset_version = $detail.version]}' --slurp ./downloads/*/metadata.json > washington_dataset_boundaries.geojson

 Gemini answer
 jq '
  .dataset_detail as $detail |
  .dataset_detail.dataset_area.features[] |
  .properties.dataset_name = $detail.name |
  .properties.dataset_version = $detail.version
' "metadata (4).json"