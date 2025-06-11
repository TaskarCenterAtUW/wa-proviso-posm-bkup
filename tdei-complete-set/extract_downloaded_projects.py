import zipfile
import os
from datetime import datetime, timezone

downloads_dir = './downloads'

def extract_base_zip_files():
# Walk through the downloads directory and extract all zip files
    for root, dirs, files in os.walk(downloads_dir):
        for file in files:
            if file.endswith('.zip'):
                zip_path = os.path.join(root, file)
                extract_dir = os.path.join(root, os.path.splitext(file)[0])
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                print(f'Extracted {zip_path} to {extract_dir}')

def extract_internal_zip_files():
    # Walk through internal directories and extract all zip files
    for root, dirs, files in os.walk(downloads_dir):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            for file in os.listdir(dir_path):
                if file.endswith('.zip'):
                    zip_path = os.path.join(dir_path, file)
                    extract_dir = os.path.join(dir_path, os.path.splitext(file)[0])
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    print(f'Extracted {zip_path} to {extract_dir}')

def collect_all_geojson_paths():
    geojson_paths = []
    for root, dirs, files in os.walk(downloads_dir):
        for file in files:
            if file.endswith('.geojson'):
                geojson_paths.append(os.path.join(root, file))
    return geojson_paths

# all_geojson_paths = collect_all_geojson_paths()
# print(len(all_geojson_paths))
# # Get first two geojson files
# output_file = 'washington_combined.pmtiles'
# input_file = ' '.join(all_geojson_paths[:2])
# base_command = f'tippecanoe --force --no-tile-size-limit -zg -o {output_file} {input_file}'
# print(base_command)

# import geopandas as gpd  # Example: using GeoPandas
# file_path = './downloads/00fe9710-73fe-4cc5-8625-57e7ccb3672c/san-juan-county/san-juan-county.nodes.geojson'
# gdf = gpd.read_file(file_path)
# print(gdf.head())

def write_last_updated(filename='last_updated.txt'):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs(downloads_dir, exist_ok=True)
    filepath = os.path.join(downloads_dir, filename)
    try:
        with open(filepath, 'w') as ts_file:
            ts_file.write(f"{timestamp}\n")
        print(f'Created {filepath} with timestamp {timestamp}')
    except Exception as e:
        print(f'Error writing timestamp file {filepath}: {e}')

if __name__ == "__main__":
    extract_base_zip_files()
    extract_internal_zip_files()
    all_geojson_paths = collect_all_geojson_paths()
    print(f'Total geojson files found: {len(all_geojson_paths)}')
    write_last_updated()
