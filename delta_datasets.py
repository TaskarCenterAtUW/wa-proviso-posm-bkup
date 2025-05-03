
import requests
import pymongo
from dotenv import load_dotenv
import os
from tqdm import tqdm
load_dotenv()

mongo_db_connection =os.getenv('MONGO_DB_CONNECTION')

base_url = os.getenv('BASE_URL')


db_client = pymongo.MongoClient(mongo_db_connection)
db = db_client['wa-proviso-2']
db_collection = db['tdei_datasets']

pipeline = [
    {
        '$match': {
            'environment': 'prod'
        }
    },
    {
        
        '$group': {
            '_id': '$project_id', 
            'datasets': {
                '$push': {
                    'name': '$metadata.dataset_detail.name', 
                    'version': '$metadata.dataset_detail.version'
                }
            }
        }
    }, {
        '$unwind': '$datasets'
    }, {
        '$group': {
            '_id': {
                'project_id': '$_id', 
                'dataset_name': '$datasets.name'
            }, 
            'versions': {
                '$addToSet': '$datasets.version'
            }
        }
    }, {
        '$project': {
            '_id': 0, 
            'project_id': '$_id.project_id', 
            'dataset_name': '$_id.dataset_name', 
            'versions': 1
        }
    }
]

# Each project contains project_id, dataset_name, and versions as a list
projects = list(db_collection.aggregate(pipeline))


# all_projects = list(remote_tiles_collection.aggregate(pipeline))

# #remove duplicates from projects
# projects = []
# for project in all_projects:
#     if project not in projects: # how does this work?
#         projects.append(project)

def get_user_token(username,password):
    url = f'{base_url}/auth/login'
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        'email': username,
        'password': password
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return None
    return response.json()['access_token']

def get_datasets_from_search(name, token):
    url = f'{base_url}/datasets/search'
    headers = {
        'Authorization': 'Bearer '+token,
        "Content-Type": "application/json"
    }
    params = {
        'query': name,
        'env': 'prod'
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return []
    # Check if the response is empty
    if not response.json():
        print(f"No datasets found for name: {name}")
        return []
    # Check if the response is a list
    if not isinstance(response.json(), list):
        print(f"Unexpected response format for name: {name}")
        return []
    # Check if the response contains the expected keys
    return_datasets = []
    for dataset in response.json():
        if 'metadata' not in dataset or 'dataset_detail' not in dataset['metadata']:
            print(f"Unexpected dataset format for name: {name}")
            continue
        else:
            # Check if the dataset_detail contains the expected keys
            if 'name' not in dataset['metadata']['dataset_detail'] or 'version' not in dataset['metadata']['dataset_detail']:
                print(f"Unexpected dataset_detail format for name: {name}")
                continue
            else:
                dataset_name = dataset['metadata']['dataset_detail']['name']
                if dataset_name == name:
                    return_datasets.append(dataset)
    return return_datasets

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
        'Authorization': access_token,
        "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json()

def link_dataset_to_project(dataset_id, project_id, token, environment):
    url = f'{base_url}/projects/{project_id}/assign-tdei-dataset'
    headers = {
        'Authorization': 'Bearer '+token,
        "Content-Type": "application/json"
    }
    data = {
        'dataset_id': dataset_id,
        'environment': environment
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return None
    return response.json()


# get the delta dataset between filtered_datasets and linked_datasets by checking the version
def get_delta_dataset(filtered_datasets, linked_versions, project_id):
    # Collect versions from linked datasets
    # linked_versions = set()
    # for ds in linked_datasets:
    #     try:
    #         version = ds['metadata']['dataset_detail']['version']
    #         linked_versions.add(version)
    #     except (KeyError, TypeError) as e:
    #         print(f"⚠️ Error in project '{project['project_id']}' with dataset ID '{ds.get('tdei_dataset_id', 'unknown')}' → {e}")
    #         continue

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
            'environment': 'prod'
            
        })
        except (KeyError, TypeError) as e:
            # print error message to which where it wrong
            print(f"⚠️ Error in project '{project['project_id']}' with dataset ID '{ds.get('tdei_dataset_id', 'unknown')}' → {e}")
            continue
      
    return delta_datasets  

def get_total_delta_datasets(available_projects_with_versions, mc_access_token):
    total_delta_datasets = 0
    datasets_to_link = []
    # projects has mc_project_id and tdei_dataset_name 
    # for index, project in enumerate(projects, start=1):
    for project in tqdm(available_projects_with_versions):
        # search for datasets with the same tdei_dataset_name
        search_result_datasets = get_datasets_from_search(project['dataset_name'], mc_access_token)
        # Get the datasets with the exact same name 
        # filtered_datasets = filter_datasets_by_name(search_result_datasets, project['dataset_name'])
        # Get the linked datasets by project_id
        # linked_datasets = get_dataset_by_project_id(project['project_id'])
        # Fetch the pending datasets to be linked
        delta_datasets = get_delta_dataset(search_result_datasets, project['versions'], project['project_id'])

        delta_count = len(delta_datasets)
        # Skip projects with zero delta datasets to save time
        if delta_count == 0:
            # print(f"Project  - {project['dataset_name']} - skipped")
            continue
        else:
            # Add the delta datasets to the list of datasets to link
            datasets_to_link.extend(delta_datasets)
        total_delta_datasets += delta_count
        
        # print(f"Project  | project name: {project['dataset_name']} | project delta version count {len(delta_datasets)} - Total Delta Datasets Count: {total_delta_datasets}")

    return datasets_to_link


# total_datasets = get_total_delta_datasets()
# print(f'Total Delta Datasets: {total_datasets}')

def main():
    # Get the projects with proper versions
    projects_with_versions = [project for project in projects if len(project['versions'])>0]
    username = os.getenv('MC_USERNAME')
    password = os.getenv('MC_PASSWORD')
    # Get the access token
    token = get_user_token(username, password)
    if token is None:
        print("Failed to get access token")
        return
    total_delta_datasets = get_total_delta_datasets(projects_with_versions,token)
    print(f'Total Datasets to be linked: {len(total_delta_datasets)}')
    for to_link_dataset in tqdm(total_delta_datasets, desc="Linking datasets"):
        # link the dataset to the project
        response = link_dataset_to_project(to_link_dataset['tdei_dataset_id'], to_link_dataset['mc_project_id'], token, to_link_dataset['environment'])
        if response is None:
            print(f"Failed to link dataset {to_link_dataset['tdei_dataset_id']} to project {to_link_dataset['mc_project_id']}")
            continue
    # for project in projects_with_versions:
        # print(project)

if __name__ == "__main__":
    main()

