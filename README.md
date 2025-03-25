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