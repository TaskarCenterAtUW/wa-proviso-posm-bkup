from generate_county_datasets import generate_metadata_file
import os
from tdei_service import TDEIService
import shutil
import json
from mission_control_service import MissonControlService
import time


# Start with generation of boundary and metadata files
# Start time for reference
start_time = time.time()
county_name = 'benton'
input_files_folder = 'counties'
dow_file_name = f'dow-{county_name.title()}.geojson'
boundary_file_name = f'{county_name.title()}.geojson'
boundary_path = os.path.join('counties', boundary_file_name)
dow_path = os.path.join('counties', dow_file_name)

# Configuration for TDEI service
tdei_service = TDEIService()
username = os.getenv('TDEI_USERNAME')
password = os.getenv('TDEI_PASSWORD')
environment = os.getenv('TDEI_ENVIRONMENT','stage')
project_group_id = os.getenv('TDEI_PROJECT_GROUP_ID','b8098696-7588-4278-beb8-a730d33a71cc') # GS_WSP_PG in Stage
service_id = os.getenv('TDEI_SERVICE_ID','d1199d1a-495b-43a0-b7cd-1f941a657356') # Proviso_Unions
# print(f' Getting creds for {username} in {environment} environment with password {password}')
access_token = tdei_service.get_access_token(environment,username,password)
print(f'Access token: {access_token}')

# Generate the metadata and boundary file for the same.
metadata_content = generate_metadata_file(boundary_path, dow_path, county_name.title(),tdei_service,environment=environment,tdei_project_group_id=project_group_id)
output_dir = os.path.join("../output/county-datasets", county_name)
# Create the output directory if it does not exist
os.makedirs(output_dir, exist_ok=True)
# Get the dataset version if already exists
metadata_file_path =  os.path.join("../output/county-datasets", county_name,
                                    f'{county_name}-metadata.json')
# Write the metadata file
with open(metadata_file_path, 'w') as metadata_file:
    json.dump(metadata_content, metadata_file, indent=4)

# copy boundary dow_file name to output directory with dataset_name-boundary.json
output_boundary_path = os.path.join("../output/county-datasets", county_name, f'{county_name}-dow-boundary.geojson')
shutil.copy(dow_path, output_boundary_path)

# Start with the mc project job
mc_project_ids_file = 'counties-mc-ids.json'
# Load the project ids from the file
with open(mc_project_ids_file, 'r') as f:
    mc_project_ids = json.load(f)
# Get the project id for the county
mc_project_id_for_county = mc_project_ids.get(county_name, None)
if mc_project_id_for_county is None:
    print(f'No MC project id found for {county_name}.')
    # probably break here.

# Initiate a job in mission Control service to upload the county dataset.

mission_control_service = MissonControlService(project_group_id=project_group_id, service_id=service_id)
try:
    mc_job_id = mission_control_service.initiate_dataset_upload_job(
        dataset_name=county_name.title(),
        working_dir=output_dir,
        access_token=access_token,
        mc_project_id=mc_project_id_for_county,
        environment=environment
    )
    print(f'Job initiated successfully with ID: {mc_job_id}')
    mc_start_time = time.time()
    tdei_job_id = mission_control_service.get_job_result(project_id=mc_project_id_for_county, flow_id=mc_job_id)
    mc_time_taken = time.time() - mc_start_time
    print(f'MC Job completed in {mc_time_taken:.2f} seconds.')
    print("Job ID:", tdei_job_id)
    # Wait for the completion of TDEI Job ID also
    if tdei_job_id:
        print(f'TDEI Job ID: {tdei_job_id} in environment {environment}')
        tdei_job_result = tdei_service.wait_for_job_completion(access_token,environment,tdei_job_id,project_group_id)
        print('TDEI Job Result:', tdei_job_result)
        time_taken = time.time() - start_time
        print(f'TDEI Job completed in {time_taken:.2f} seconds.')
        report_file = os.path.join(output_dir, f'{county_name}-report.txt')
        with open(report_file, 'w') as report:
            report.write(f'MC Job ID: {mc_job_id}\n')
            report.write(f'MC Job Result: {mc_job_id}\n')
            report.write(f'Time taken for MC Job: {mc_time_taken:.2f} seconds\n')
            report.write(f'TDEI Job ID: {tdei_job_id}\n')
            report.write(f'TDEI Job Result: {tdei_job_result}\n')
            report.write(f'Time taken for TDEI Job: {time_taken:.2f} seconds\n')
           
        print(f'Report written to {report_file}')
    else:
        print('No TDEI Job ID returned.')
except Exception as e:
    print(f'Error initiating job: {e}')
    exit(1)