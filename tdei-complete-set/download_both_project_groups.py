import os
import json
from fetch_all_projects import TDEIDatasetDownloader
from tqdm import tqdm
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

load_dotenv()

def main():
    print("Fetching datasets for both project groups...")
    reports_output_folder = 'report-downloads'
    if not os.path.exists(reports_output_folder):
        os.makedirs(reports_output_folder)

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

    tqdm.pandas()

    for pg_name, pg_data in project_groups.items():
        print(f"\nProcessing project group: {pg_name}")
        
        datasets = downloader.get_latest_datasets(pg_data['query_params'])
        datasets['project_group'] = pg_name
        datasets['qm'] = datasets['tdei_dataset_id'].progress_apply(downloader.fetch_quality_metric)

        if datasets is not None and not datasets.empty:
            # 1. Save full JSON
            output_json = f'{pg_name}_datasets.json'
            output_json_path = os.path.join(reports_output_folder, output_json)
            datasets.to_json(output_json_path, orient='records', indent=4)
            print(f"Saved full dataset to {output_json_path}")

            # 2. Save per-project CSV files
            project_folder = os.path.join(reports_output_folder, f"{pg_name}_projects_csv")
            os.makedirs(project_folder, exist_ok=True)

            for service_id, group_df in datasets.groupby("service"):
                if not service_id or pd.isna(service_id):
                    continue  # skip missing service values

                rows_for_csv = []
                for _, row in group_df.iterrows():
                    rows_for_csv.append({
                        "name": row["name"],
                        "version": row["version"],
                        "upload_date": row["upload_date"],
                        "tdei_dataset_id": row["tdei_dataset_id"],
                        "service": row["service"],
                        "project_group": row["project_group"],
                        "surface_percentage": row["qm"].get("surface_percentage"),
                        "width_percentage": row["qm"].get("width_percentage"),
                        "incline_percentage": row["qm"].get("incline_percentage"),
                        "length_percentage": row["qm"].get("length_percentage"),
                    })

                df_csv = pd.DataFrame(rows_for_csv)
                csv_path = os.path.join(project_folder, f"{service_id}.csv")
                df_csv.to_csv(csv_path, index=False)

            print(f"Saved project-wise CSV files under {project_folder}")
        else:
            print(f"No datasets found for {pg_name}. Skipping file creation.")

        # 3. Update last_updated.txt
        timestamp_file_path = os.path.join(reports_output_folder, 'last_updated.txt')
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(timestamp_file_path, 'w') as f:
            f.write(now)
        print(f"Updated timestamp written: {now}")

        print(f"Completed for {pg_name}")

    print("\nAll project groups processed successfully.")

if __name__ == "__main__":
    main()
