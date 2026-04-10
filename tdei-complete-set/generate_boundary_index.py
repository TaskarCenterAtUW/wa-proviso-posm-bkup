import geopandas as gpd
import pandas as pd
import json
import argparse
import os




def parse_args():
    parser = argparse.ArgumentParser(description="Generate Index file for boundary geojson")
    parser.add_argument("-b","--boundary_file", default="washington_dataset_boundaries.geojson")
    parser.add_argument("-o","--output_index", default="washington_dataset_boundaries_index.json")
    return parser.parse_args()


def main():
    args = parse_args()
    boundary_file = args.boundary_file
    output_path = args.output_index
    # Check for file
    if not os.path.exists(boundary_file):
        print(f"Boundary file {boundary_file} does not exist.")
        return
    boundary_gdf = gpd.read_file(boundary_file)
    boundary_gdf_clipped = boundary_gdf[['name','tdei_dataset_id','geometry','upload_date','version','tcat_quality_report_url','tcat_quality_report_url_pdf']]
    boundary_gdf_clipped['upload_date'] = pd.to_datetime(boundary_gdf_clipped['upload_date']).dt.strftime('%Y-%m-%dT%H:%M:%S%z') #2026-02-03T14:13:45.183Z
    geojson_data = boundary_gdf_clipped.to_json(show_bbox=True)
    geojson_json_data = json.loads(geojson_data)
    features = geojson_json_data['features']
    index_items = []
    for feature in features:
        index_item = {
            "name": feature['properties']['name'],
            "upload_date": feature['properties']['upload_date'],
            "version": feature['properties']['version'],
            "tdei_dataset_id": feature['properties']['tdei_dataset_id'],
            "tcat_quality_report_url": feature['properties']['tcat_quality_report_url'] if 'tcat_quality_report_url' in feature['properties'] else None,
            "tcat_quality_report_url_pdf": feature['properties']['tcat_quality_report_url_pdf'] if 'tcat_quality_report_url_pdf' in feature['properties'] else None,
            "tcat_quality_report_url_html": feature['properties']['tcat_quality_report_url_html'] if 'tcat_quality_report_url_html' in feature['properties'] else None,
            "bbox": {
                "minLng": feature['bbox'][0],
                "maxLng": feature['bbox'][2],
                "minLat": feature['bbox'][1],
                "maxLat": feature['bbox'][3]
            }
        }
        index_items.append(index_item)
    with open(output_path, 'w') as f:
        json.dump(index_items, f, indent=2)




if __name__ == "__main__":
    main()