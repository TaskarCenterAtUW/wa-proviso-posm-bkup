import sys
import json
import asyncio
import os
# from osm-convert import Formatter
# from osm-convert import Formatter
from datetime import datetime, timedelta
from tdei_service import TDEIService

from osm_osw_reformatter import Formatter

import zipfile


def download_osm_file(file_path, dataset_name):
    working_dir = os.path.join("../output/county-datasets", dataset_name)
    zip_file_path = os.path.join(working_dir, f'{dataset_name}.zip')
    if os.path.exists(zip_file_path):
        print(f'Zip file {zip_file_path} already exists. Skipping download and processing for {dataset_name}')
        return 
    f = Formatter(workdir=working_dir, file_path=file_path)
    result = asyncio.run(f.osm2osw())
    # zip them 
    
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for file in result.generated_files:
            # Add the file to the zip file
            file_basename = os.path.basename(file)
            # remove prefix final. 
            if file_basename.startswith('final.'):
                file_basename = file_basename[len('final.'):]
            zipf.write(file, file_basename)
            print(f'Added {file} to {zip_file_path}')
    print(f'Generated zip file at {zip_file_path}')



def generate_metadata_file(boundary_file_path,dow_file_path ,dataset_name, service: TDEIService = None, environment:str = 'prod'):

    with open(boundary_file_path, 'r') as file:
        boundary_data = json.load(file)
    with open(dow_file_path, 'r') as file:
        dow_data = json.load(file)
    dataset_name_without_space = dataset_name.replace(' ', '_')

    # Get the current version from service
    latest_version = 1.0
    full_dataset_name = f'GS_{dataset_name_without_space}_County'
    if service:
        latest_version = service.get_current_version(environment,full_dataset_name)
        print(f'Latest version for {full_dataset_name} is {latest_version}')
        if latest_version is not None:
            print(latest_version)
            latest_version += 0.01
    else:
        print(f'Service is not provided. Using default version {latest_version}')


    release_notes = f'Dataset covering all the incoprorated areas of {dataset_name} county. The dataset area is based on incorporated areas. The `area` tag in custom_metadata is the complete county boundary.'
    current_date = datetime.now()
    json_dict = {}
    json_dict['data_provenance'] = {}
    json_dict['dataset_detail'] = {}
    json_dict['dataset_summary'] = {}
    json_dict['dataset_detail']['custom_metadata'] = {}
    json_dict['data_provenance']['full_dataset_name'] = full_dataset_name
    json_dict['data_provenance']['allow_crowd_contributions'] = True
    json_dict['dataset_detail']['name'] = full_dataset_name
    json_dict['dataset_detail']['description'] = f'''OSW v0.2 compliant dataset for {dataset_name}'''
    json_dict['dataset_detail']['version'] = f'{latest_version:.1f}'
    json_dict['dataset_detail']['collected_by'] = "GS and UW"
    json_dict['dataset_detail']['collection_date'] = current_date.isoformat()
    json_dict['dataset_detail']['valid_from'] = current_date.isoformat()
    
    two_years_from_now = current_date.replace(year=current_date.year + 2)
    json_dict['dataset_detail']['valid_to'] = two_years_from_now.isoformat()
    json_dict['dataset_detail']['collection_method'] = "others"
    json_dict['dataset_detail']['custom_metadata']['pipeline version'] = '2.0'
    json_dict['dataset_detail']['custom_metadata']['area'] = boundary_data
    json_dict['dataset_detail']['custom_metadata']['county'] = dataset_name
    json_dict['dataset_detail']['data_source'] = "InHouse"
    json_dict['dataset_detail']['dataset_area'] = dow_data
    json_dict['dataset_detail']['schema_version'] = "v0.2"
    json_dict['dataset_summary']['release_notes'] = release_notes
    json_dict['dataset_summary']['county'] = dataset_name
    return json_dict
    

def main(osmfile):
    # Check if its a directory
    # Get the name from the file based on first [.]
    files_to_process = []
    if os.path.isdir(osmfile):
        # If it is a directory, get all the files in the directory
        osmfiles = [os.path.join(osmfile, f) for f in os.listdir(osmfile) if f.endswith('.pbf')]
        for osmfile in osmfiles:
            files_to_process.append(osmfile)
    else:
        files_to_process.append(osmfile)
    
    tdei_service = TDEIService()
    username = os.getenv('TDEI_USERNAME')
    password = os.getenv('TDEI_PASSWORD')
    environment = os.getenv('TDEI_ENVIRONMENT','prod')
    service_id = os.getenv('TDEI_SERVICE_ID','d1199d1a-495b-43a0-b7cd-1f941a657356')
    access_token = tdei_service.get_access_token(environment,username,password)
    print(f'Access token: {access_token}')

    # Loop through the files and process them
    for osmfile in files_to_process:
        # Get the name of the file without the extension
        dataset_name = os.path.basename(osmfile).split('.')[0]
        if dataset_name == 'complete':
            print(f'Skipping complete dataset {osmfile}')
            continue
        print("Processing %s" % osmfile)
        download_osm_file(osmfile, dataset_name)
        # Generate the metadata file
        # boundary_file_path = os.path.join(os.path.dirname(osmfile), f'{dataset_name}-boundary.geojson')
        print(f'Processing for {dataset_name.title()}')
        dow_file_name = f'dow-{dataset_name.title()}.geojson'
        boundary_file_name = f'{dataset_name.title()}.geojson'
        boundary_path = os.path.join('counties', boundary_file_name)
        dow_path = os.path.join('counties', dow_file_name)
        if not os.path.exists(boundary_path):
            print(f'Boundary file {boundary_path} does not exist. Skipping {dataset_name.title()}')
            continue
        metadata_content = generate_metadata_file(boundary_path, dow_path, dataset_name.title(),tdei_service)
        # Get the dataset version if already exists
        metadata_file_path =  os.path.join("../output/county-datasets", dataset_name,
                                           f'{dataset_name}-metadata.json')
        # Write the metadata file
        with open(metadata_file_path, 'w') as metadata_file:
            json.dump(metadata_content, metadata_file, indent=4)
    
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python %s <osmfile>" % sys.argv[0])
        sys.exit(-1)
    sys.exit(main(sys.argv[1]))