import time
from fetch_all_projects import TDEIDatasetDownloader
import os
import json


if __name__ == '__main__':
    old_datasets_json = 'tdei_datasets_unions.json'
    new_datasets_json = 'tdei_datasets_unions_updated.json'
    with open(old_datasets_json, 'r') as f:
        old_datasets = json.load(f)
    with open(new_datasets_json, 'r') as f:
        new_datasets = json.load(f)
    print(f"Old datasets count: {len(old_datasets)}")
    print(f"New datasets count: {len(new_datasets)}")
    dataset_name = 'GS_Raymond_City'
    # Get the dataset_id from old datasets
    old_dataset_id = None
    new_dataset_id = None
    old_datasets_set = {dataset['name']: dataset for dataset in old_datasets}
    with open('dataset_comparison_unions.txt', 'w') as log_file:
        for dataset in new_datasets:
            name = dataset['name']
            if name in old_datasets_set:
                old_dataset = old_datasets_set[name]
                old_dataset_id = old_dataset['tdei_dataset_id']
                new_dataset_id = dataset['tdei_dataset_id']
                old_dataset_version = old_dataset['version']
                new_dataset_version = dataset['version']
                if old_dataset_id != new_dataset_id:
                    print(f"Dataset '{name}' has a new dataset ID {new_dataset_id}.")
                if old_dataset_version != new_dataset_version:
                    print(f"Dataset '{name}' has a new version {new_dataset_version}.")
                log_file.write(f'{old_dataset_id}, {new_dataset_id}, {name}, {old_dataset_version}, {new_dataset_version}\n')
    # for dataset in old_datasets:
    #     if dataset['name'] == dataset_name:
    #         old_dataset_id = dataset['tdei_dataset_id']
    #         old_dataset_version = dataset['version']
    #         break
    # for dataset in new_datasets:
    #     if dataset['name'] == dataset_name:
    #         new_dataset_id = dataset['tdei_dataset_id']
    #         new_dataset_version = dataset['version']
    #         break
    # print(f"Old dataset ID for {dataset_name}: {old_dataset_id}")
    # print(f"New dataset ID for {dataset_name}: {new_dataset_id}")
    # print(f"Old dataset version for {dataset_name}: {old_dataset_version}")
    # print(f"New dataset version for {dataset_name}: {new_dataset_version}")