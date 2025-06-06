import os
from fetch_all_projects import TDEIDatasetDownloader
from tqdm import tqdm
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

downloader = TDEIDatasetDownloader()

username = os.getenv('TDEI_USERNAME')
password = os.getenv('TDEI_PASSWORD')

access_token = downloader.get_access_token(username, password)


project_groups = {
    "GS_WSP_PG": {
        "id": "1dd7c38e-c7a6-4e3a-be8b-379f823a7ad7",
        "query_params": {
            'page_no': 1,
            'page_size': 50,
            'tdei_project_group_id': "1dd7c38e-c7a6-4e3a-be8b-379f823a7ad7",
            'data_type': 'osw',
            'sort_field': 'uploaded_timestamp',
            'sort_order': 'asc'
        }
    },
    "TCAT_WSP_PG": {
        "id": "0eace285-430b-4f3e-bd76-d102a2c5385c",
        "query_params": {
            'page_no': 1,
            'page_size': 50,
            'tdei_project_group_id': "0eace285-430b-4f3e-bd76-d102a2c5385c",
            'data_type': 'osw',
            'sort_field': 'uploaded_timestamp',
            'sort_order': 'asc',
            'status': 'Publish'
        }
    }
}

for pg_name, pg_data in project_groups.items():
    print(f"Processing project group: {pg_name}")
    
    datasets = downloader.get_latest_datasets(pg_data['query_params'])
    output_json = f'{pg_name}_datasets.json'

    if datasets is not None and not datasets.empty:
        datasets.to_json(output_json, orient='records', indent=4)
        print(f"Saved {output_json}")
    else:
        print(f"No datasets found for {pg_name}. Skipping file creation.")

    print(f"Completed for {pg_name}\n")
