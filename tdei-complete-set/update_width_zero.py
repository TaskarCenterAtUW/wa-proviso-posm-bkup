
import time
from fetch_all_projects import TDEIDatasetDownloader
import os
import zipfile
import json
import subprocess
import tempfile
import shutil
from datetime import datetime, timedelta
import requests
from tqdm import tqdm
def check_if_dataset_has_zero_widths(dataset_zip_path:str, working_dir:str = './temp_dataset') -> bool:
    # extract the zip file to a temporary directory
    if not os.path.exists(dataset_zip_path):
        print(f"Dataset zip file {dataset_zip_path} does not exist.")
        return False
    with zipfile.ZipFile(dataset_zip_path, 'r') as zip_ref:
        zip_ref.extractall(working_dir)

    # get the zip file within the extracted directory that contains .zip extension
    inner_zip_path = None
    for root, dirs, files in os.walk(working_dir):
        for file in files:
            if file.endswith('.zip'):
                inner_zip_path = os.path.join(root, file)
                break
        if inner_zip_path:
            break
    if not inner_zip_path:
        print(f"No inner zip file found in {dataset_zip_path}")
        return False
    # extract the inner zip file
    with zipfile.ZipFile(inner_zip_path, 'r') as zip_ref:
        zip_ref.extractall(working_dir)

    # Get the path to edges file (file with 'edges' in its name)
    edges_file_path = None
    for root, dirs, files in os.walk(working_dir):
        for file in files:
            if 'edges' in file and file.endswith('.geojson'):
                edges_file_path = os.path.join(root, file)
                break
        if edges_file_path:
            break

    if not edges_file_path:
        print(f"No edges file found in {dataset_zip_path}")
        return False

    jq_command = ['jq', '[.features[] | select(.properties.width? == 0 and .properties.footway? == "sidewalk")] | length', edges_file_path]
    try:
        result = subprocess.run(jq_command, capture_output=True, text=True, check=True)
        if result.stdout:
            zero_width_count = int(result.stdout.strip())
            if zero_width_count > 0:
                print(f"Number of edges with zero width: {zero_width_count}")
                return True
            else:
                print(f"No edges with zero width found in {dataset_zip_path}")
                return False
        else:
            print(f"Dataset {dataset_zip_path} has no edges with zero width.")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Error running jq command: {e}")
        return False


def update_width_to_default(old_edges_file_path: str, new_edges_file_path: str):
    jq_query = '''
        .features |= map(
            if .properties.footway? == "sidewalk" then
                # Only if footway is sidewalk, we check width
                .properties.width = if (.properties.width? == 0 or .properties.width? == null) then 1.33 else .properties.width end
            else
                # If footway is not "sidewalk", return the feature unchanged
                .
            end
        )
    '''
    jq_command = [
        'jq',
        jq_query,
        old_edges_file_path
    ]
    try:
        result = subprocess.run(jq_command, capture_output=True, text=True, check=True)
        with open(new_edges_file_path, 'w') as new_file:
            new_file.write(result.stdout)
        print(f"Updated edges file saved to {new_edges_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error running jq command: {e}") 


def update_metadata_file(metadata_path:str):
    '''
    Update the metadata file with the new version and release notes.
    Changes the version number by 0.1, updates the collection date, valid from and valid to dates,
    Args:        metadata_path (str): Path to the metadata file.
    Returns:     dict: Updated metadata dictionary.
    '''
    # Load the metadata file
    with open(metadata_path, 'r') as file:
        metadata = json.load(file)
    # Get the version from the metadata file.
    current_version = metadata.get('dataset_detail', {}).get('version', '1.0')
    print(f"Current version: {current_version}")
    # Update the float number by 0.1
    new_version = str(float(current_version) + 0.1)
    print(f"New version: {new_version}")
    # ensure new version is upto 1 decimal places maximum
    new_version = f"{float(new_version):.1f}"
    current_date = datetime.now()
    two_years_from_now = current_date.replace(year=current_date.year + 2)
    metadata['dataset_detail']['version'] = new_version
    metadata['dataset_detail']['collection_date'] = current_date.isoformat()
    metadata['dataset_detail']['valid_from'] = current_date.isoformat()
    metadata['dataset_detail']['valid_to'] = two_years_from_now.isoformat()
    # Update the release notes
    release_notes = 'Updated the default width of edges with zero width to 1.33 meters.'
    metadata['dataset_summary']['release_notes'] = release_notes
    return metadata



def upload_tdei_dataset(token:str,environment:str,dataset_file:str,metadata_file:str,tdei_project_group:str,tdei_service_id:str):
         '''
         Uploads the TDEI dataset to the storage. and fetches the jobId from upload
         '''
         try:
            #   self.check_access_token_validity(token,environment)
              # Get the local meta file content json
              base_url = 'https://api.tdei.us'
              if base_url is None:
                  raise ValueError(f'Invalid environment: {environment}')
              else:
                   upload_url = f'{base_url}/api/v1/osw/upload/{tdei_project_group}/{tdei_service_id}'
                   print(f'Uploading to {upload_url}')
                   # Upload multi-part form data
                   files = {
                    'dataset': open(dataset_file, 'rb'),
                    'metadata': open(metadata_file, 'rb')
                    }
                   headers = {    
                        'Authorization': f'Bearer {token}'
                     }
                   response = requests.post(upload_url, headers=headers, files=files)
                #    print(response.text)
                   if response.status_code == 202:
                        jobId = response.text
                        print(f'Job ID: {jobId}')
                        return jobId
                   else: 
                        print(response.text)
                        raise ValueError(f'Failed to upload dataset. Received response code {response.status_code} and response {response.text}')

         except ValueError as e:
              print(f'Error: {e}')
              raise e

def process_one_dataset(dataset_id:str, dataset_name:str):
    temp_dir = tempfile.mkdtemp()
    dataset_zip_path = f'./downloads/{dataset_id}.zip'
    has_zero_widths = check_if_dataset_has_zero_widths(dataset_zip_path, working_dir=temp_dir)
    if has_zero_widths:
        # Get the edges file path
        edges_file_path = None
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if 'edges' in file and file.endswith('.geojson'):
                    edges_file_path = os.path.join(root, file)
                    break
            if edges_file_path:
                break
        if not edges_file_path:
            print(f"No edges file found in {dataset_zip_path}")
            return
        print(f"Edges file found: {edges_file_path}")
        original_dataset_dir = f'./downloads/{dataset_id}'
        if not os.path.exists(original_dataset_dir):
            os.makedirs(original_dataset_dir)
        edges_file_name = os.path.basename(edges_file_path)
        updated_edges_file_path = os.path.join(original_dataset_dir, edges_file_name)
        update_width_to_default(f'{edges_file_path}', f'{updated_edges_file_path}')
        new_metadata = update_metadata_file(f'{temp_dir}/metadata.json')
        with open(f'{original_dataset_dir}/metadata.json', 'w') as file:
            json.dump(new_metadata, file, indent=4)
        # Copy all the contents of temp_dir to the original dataset directory and ignore if the file already exists
        for item in os.listdir(temp_dir):
            s = os.path.join(temp_dir, item)
            d = os.path.join(original_dataset_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                if not os.path.exists(d) and not s.endswith('.zip'): # ignore .zip file
                    shutil.copy2(s, d)
        # Remove the temporary directory
        shutil.rmtree(temp_dir)
        # print(f"Temporary directory {temp_dir} removed.")
        
        data_zip_path = f'{original_dataset_dir}/{dataset_id}.zip'
        # zip all the .geojson files with dataset_id.zip
        with zipfile.ZipFile(f'{data_zip_path}', 'w') as zipf:
            for root, dirs, files in os.walk(original_dataset_dir):
                for file in files:
                    if file.endswith('.geojson'):
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, original_dataset_dir))
        new_metadata_path = f'{original_dataset_dir}/metadata.json'
        new_dataset_zip_path = data_zip_path
        return {'dataset_id': dataset_id, 'dataset_name': dataset_name, 'metadata_path': new_metadata_path, 'dataset_zip_path': new_dataset_zip_path}
    else:
        print(f"Dataset {dataset_name} does not have edges with zero width. No changes made.")


def finish_all_stuff():
    datasets_json_file = 'tdei_datasets.json'
    with open(datasets_json_file, 'r') as file:
        datasets = json.load(file)
    datasets_with_zero_widths = 0
    downloader = TDEIDatasetDownloader()
    username = os.getenv('TDEI_USERNAME')
    password = os.getenv('TDEI_PASSWORD')
    access_token = downloader.get_access_token(username, password) # type: ignore
    project_group_id = '1dd7c38e-c7a6-4e3a-be8b-379f823a7ad7'
    service_id = 'a008c57d-7959-478d-97e3-b3ca4268eaa6'
    # print(f"Access token: {access_token}")
    for dataset in tqdm(datasets, desc="Processing datasets"):
        dataset_id = dataset['tdei_dataset_id']
        dataset_name = dataset['name']
        downloaded_directory = f'./downloads/{dataset_id}'
        if os.path.exists(downloaded_directory):
            print(f"Dataset {dataset_name} with ID {dataset_id} already downloaded. Skipping download.")
            continue
        result = process_one_dataset(dataset_id, dataset_name)
        if result:
            datasets_with_zero_widths += 1
            print(f"Processed dataset: {result['dataset_name']} with ID {result['dataset_id']}")
            print(f"Updated metadata file path: {result['metadata_path']}")
            print(f"Updated dataset zip file path: {result['dataset_zip_path']}")
            # Upload the dataset
            job_id = upload_tdei_dataset(access_token, 'prod', result['dataset_zip_path'], result['metadata_path'], project_group_id, service_id)
            print(f"Dataset {result['dataset_name']} with ID {result['dataset_id']} uploaded successfully. Job ID: {job_id}")
            # sleep for 5 seconds to avoid rate limiting
            time.sleep(5)
            # break # Uncomment this line to stop after processing the first dataset
        else:
            print(f"Dataset {dataset_name} with ID {dataset_id} does not have edges with zero width. No changes made.")
            datasets_with_zero_widths += 1
            print(f"Skipping dataset {dataset_name} with ID {dataset_id} as it does not have edges with zero width.")
            continue            
    print(f"Total datasets processed with zero widths: {datasets_with_zero_widths}")
    return datasets_with_zero_widths
        
if __name__ == '__main__':
    finish_all_stuff()