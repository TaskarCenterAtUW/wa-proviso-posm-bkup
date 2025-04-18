
import requests
import pymongo
from dotenv import load_dotenv
import os

load_dotenv()

mongo_db_connection =os.getenv('MONGO_DB_CONNECTION')
tokens = os.getenv('TDEI_API_KEY')

base_url = os.getenv('BASE_URL')


remote_db_client = pymongo.MongoClient(mongo_db_connection)
remote_db = remote_db_client['wa-proviso-2']
remote_tiles_collection = remote_db['tdei_datasets']

pipeline = [
    {
        "$project": {
            "_id": 0,
            "project_id": "$project_id",
            "name": "$metadata.dataset_detail.name"
        }
    }
]

all_projects = list(remote_tiles_collection.aggregate(pipeline))

#remove duplicates from projects
projects = []
for project in all_projects:
    if project not in projects:
        projects.append(project)

def get_datasets_from_search(name):
    url = f'{base_url}/datasets/search'
    headers = {
        'Authorization': tokens,
        "Content-Type": "application/json"
    }
    params = {
        'query': name,
        'env': 'stage'
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

# filter out the datasets whose name is not in the search result
def filter_datasets_by_name(datasets, name):
    filtered_datasets = []
    for dataset in datasets:
        if dataset['metadata']['dataset_detail']['name'] == name:
            filtered_datasets.append(dataset)
    return filtered_datasets

# get dataset by project_id from tdei_datasets projects/67d16be1a7ada07038a1e063/tdei-datasets
def get_dataset_by_project_id(project_id):
    url = f'{base_url}/projects/{project_id}/tdei-datasets'
    headers = {
        'Authorization': tokens,
        "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json()


# get the delta dataset between filtered_datasets and linked_datasets by checking the version
def get_delta_dataset(filtered_datasets, linked_datasets, project_id):
    # Collect versions from linked datasets
    linked_versions = set()
    for ds in linked_datasets:
        try:
            version = ds['metadata']['dataset_detail']['version']
            linked_versions.add(version)
        except (KeyError, TypeError) as e:
            print(f"⚠️ Error in project '{project['project_id']}' with dataset ID '{ds.get('tdei_dataset_id', 'unknown')}' → {e}")
            continue

    # Now compare against filtered datasets
    delta_datasets = []
    for ds in filtered_datasets:
        try:
            version = ds['metadata']['dataset_detail']['version']
            if version not in linked_versions:
                  delta_datasets.append({
            'tdei_dataset_id': ds['tdei_dataset_id'],
            'version': ds['metadata']['dataset_detail']['version'],
            'mc_project_id': project_id,
            'environment': 'stage'
            
        })
        except (KeyError, TypeError) as e:
            # print error message to which where it wrong
            print(f"⚠️ Error in project '{project['project_id']}' with dataset ID '{ds.get('tdei_dataset_id', 'unknown')}' → {e}")
            continue
      
    return delta_datasets  

def get_total_delta_datasets():
    total_delta_datasets = 0
    for index, project in enumerate(projects, start=1):
        
        search_result_datasets = get_datasets_from_search(project['name'])

        filtered_datasets = filter_datasets_by_name(search_result_datasets, project['name'])

        linked_datasets = get_dataset_by_project_id(project['project_id'])

        delta_datasets = get_delta_dataset(filtered_datasets, linked_datasets, project['project_id'])

        delta_count = len(delta_datasets)
        # Skip projects with zero delta datasets to save time
        if delta_count == 0:
            print(f"Project {index}/{len(projects)} - {project['name']} - skipped")
            continue

        total_delta_datasets += delta_count
        
        print(f"Project {index}/{len(projects)} | project name: {project['name']} | project delta version count {len(delta_datasets)} - Total Delta Datasets Count: {total_delta_datasets}")

    return total_delta_datasets


total_datasets = get_total_delta_datasets()
print(f'Total Delta Datasets: {total_datasets}')


