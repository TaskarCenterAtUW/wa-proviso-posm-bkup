import json
import os

counties_folder = 'counties'
# walk through the counties folder and get all the files
files = []
for root, dirs, filenames in os.walk(counties_folder):
    for filename in filenames:
        if filename.endswith('.geojson') and filename.startswith('dow-'):
            files.append(os.path.join(root, filename))
# create a config file with the files
config = {
    "directory":"./"
}

'''
{
        "output":"king_county_full.osm.pbf",
        "description":"Extract of King County, WA",
        "polygon":{
            "file_name":"king-county-boundary.geojson",
            "type":"geojson"
        }
    }
'''
extracts = []
for file in files:
    # get the name of the file without the extension
    name = os.path.splitext(os.path.basename(file))[0]
    # get the name of the file with the extension
    name_with_extension = os.path.basename(file)
    # add the file to the config
    name_lower = name.lower()
    name_lower = name_lower.replace('dow-', '')
    extract = {
        "output": f"{name_lower}.osm.pbf",
        "description": f"Extract of {name}",
        "polygon": {
            "file_name": file,
            "type": "geojson"
        }
    }
    extracts.append(extract)
config['extracts'] = extracts
print(json.dumps(config, indent=4))
# save the config to a file
with open('counties-config.json', 'w') as f:
    json.dump(config, f, indent=4)