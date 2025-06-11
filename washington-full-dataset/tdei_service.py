import requests
# from requests import status_codes
import json
import os
from dotenv import load_dotenv
load_dotenv()
import time

class TDEIService:
    
    auth_path = '/api/v1/authenticate'
    datasets_path = '/api/v1/datasets'
    
    '''
    Service used to interact with the TDEI module.
    '''
    def __init__(self):
         print(f'TDEIService initialized')
         self.base_urls = {
             'stage': 'https://api-stage.tdei.us',
             'prod': 'https://api.tdei.us',
             'dev': 'https://api-dev.tdei.us'
         }
         pass
    
    def upload_tdei_dataset(self,token:str,environment:str,dataset_file:str,metadata_file:str,tdei_project_group:str,tdei_service_id:str):
         '''
         Uploads the TDEI dataset to the storage. and fetches the jobId from upload
         '''
         try:
              self.check_access_token_validity(token,environment)
              # Get the local meta file content json
              base_url = self.base_urls.get(environment,None)
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
         
    def get_access_token(self,environment:str ,username: str, password: str):
        base_url = self.base_urls.get(environment,None)
        url = base_url + self.auth_path
        payload = {
            'username': username,
            'password': password
        }
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(url, json=payload, headers=headers)
        response.json()
        access_token = response.json()['access_token']
        self.access_token = access_token
        return access_token
    
    def get_current_version(self, environment: str, dataset_name: str, tdei_project_group_id: str = '1dd7c38e-c7a6-4e3a-be8b-379f823a7ad7'):
        #  project_group_id = '1dd7c38e-c7a6-4e3a-be8b-379f823a7ad7'
         #TODO: Hardcoded project group ID
         query_params = {
            'page_no': 1,
            'page_size': 50,
            'tdei_project_group_id':tdei_project_group_id,
            'data_type':'osw',
            'sort_field':'uploaded_timestamp',
            'full_dataset_name': dataset_name,
            'sort_order':'asc',
            'status':'All'
            }
         base_url = self.base_urls.get(environment, None)
         datasets = []
         datasets_url = base_url + self.datasets_path
         headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
         }
         page_no = 1
         page_size = 50
         response = requests.get(datasets_url,params=query_params, headers=headers)
         while True:
            if len(response.json()) >= page_size:
                print(f'Fetching page {page_no}')
                for data in response.json():
                    datasets.append({'name':data['metadata']['dataset_detail']['name'],'upload_date':data['uploaded_timestamp'],'version':data['metadata']['dataset_detail']['version'],'tdei_dataset_id':data['tdei_dataset_id']})
                page_no += 1
                query_params['page_no'] = page_no
                response = requests.get(datasets_url,params=query_params, headers=headers)
            else:
                for data in response.json():
                    datasets.append({'name':data['metadata']['dataset_detail']['name'],'upload_date':data['uploaded_timestamp'],'version':data['metadata']['dataset_detail']['version'],'tdei_dataset_id':data['tdei_dataset_id']})
                break
            print(f'Found {len(datasets)} datasets for {dataset_name}')
         if not datasets:
            print(f'No datasets found for {dataset_name}.')
            return None
         # Get the dataset version maximum
         latest_version = max(float(dataset['version']) for dataset in datasets)
         return latest_version
    
    def check_access_token_validity(self,token:str,environment:str):
         '''
         Check if the access token is valid.
         '''
         print(f'Checking token validity')
         base_url = self.base_urls.get(environment,None)
         if base_url is None:
             raise ValueError(f'Invalid environment: {environment}')
         else:
              profile_url = f'{base_url}/api/v1/api'
              headers = {
                'Authorization': f'Bearer {token}'
              }
              response = requests.get(profile_url, headers=headers)
              print(response)
              if response.status_code != 200:
                  raise ValueError(f'Invalid access token. Received response code {response.status_code}')
              else:
                   return True
    def wait_for_job_completion(self,token:str,environment:str,job_id:str, tdei_project_group_id:str='1dd7c38e-c7a6-4e3a-be8b-379f823a7ad7'):
         '''
         Waits for the job to complete and returns the job status.
         '''
         base_url = self.base_urls.get(environment,None)
         if base_url is None:
             raise ValueError(f'Invalid environment: {environment}')
         else:
              query_params = {'job_id': job_id,'tdei_project_group_id':tdei_project_group_id}
              job_status_url = f'{base_url}/api/v1/jobs'
              headers = {
                'Authorization': f'Bearer {token}'
              }
              while True:
                   response = requests.get(job_status_url, headers=headers, params=query_params)
                   if response.status_code == 200:
                        job_status = response.json()[0] if response.json() else None
                        if job_status is None:
                            print(f'Job {job_id} not found. It may have been deleted or not started yet.')
                            return None
                        # Check if the job is completed or failed
                        if job_status['status'] in ['COMPLETED', 'FAILED']:
                            return job_status
                   elif response.status_code == 404:
                        print(f'Job {job_id} not found. It may have been deleted.')
                        return None
                   else:
                        print(f'Error fetching job status: {response.text}')
                   time.sleep(5)
          

def main(action:str='upload'):
    # All the config here.
     project_group_id = '1dd7c38e-c7a6-4e3a-be8b-379f823a7ad7'
     tdei_service =  TDEIService()
     username = os.getenv('TDEI_USERNAME')
     password = os.getenv('TDEI_PASSWORD')
     environment = os.getenv('TDEI_ENVIRONMENT','prod')
     service_id = os.getenv('TDEI_SERVICE_ID','d1199d1a-495b-43a0-b7cd-1f941a657356')
     access_token = tdei_service.get_access_token(environment,username,password)
    #  print(f'Access token: {access_token}')

     if action == 'upload':
        county_datasets_output_dir = '../output/county-datasets'
        # Get the zip, metadata file for each county dataset
        processed_job_ids = []
        processed_jobs_count = 0
        

        for county in os.listdir(county_datasets_output_dir):
            county_path = os.path.join(county_datasets_output_dir, county)
            if not os.path.isdir(county_path):
                continue
            print(f'Processing county: {county}')
            metadata_file = os.path.join(county_path, f'{county}-metadata.json')
            dataset_file = os.path.join(county_path, f'{county}.zip')
            if not os.path.exists(metadata_file) or not os.path.exists(dataset_file):
                print(f'Metadata file or dataset file does not exist for {county}. Skipping.')
                continue
            print(f'Uploading dataset for {county}')
            processed_jobs_count += 1
            jobId = tdei_service.upload_tdei_dataset(access_token,environment,dataset_file,metadata_file,project_group_id,service_id)
            print(f'Job ID for {county}: {jobId}')
            processed_job_ids.append({'county':county, 'jobId': jobId})
            #  break
        print(f'Processed {processed_jobs_count} counties.')
        with open('../output/processed_jobs.json', 'w') as f:
            json.dump(processed_job_ids, f, indent=4)
     elif action == 'check_jobs':
        with open('../output/processed_jobs.json', 'r') as f:
            processed_jobs = json.load(f)
        failed_jobs = []
        failed_jobs_count = 0
        for job in processed_jobs:
            job_id = job['jobId']
            county = job['county']
            print(f'Checking job status for {county} with job ID: {job_id}')
            job_status = tdei_service.wait_for_job_completion(access_token, environment, job_id, project_group_id)
            if job_status:
                print(f'Job {job_id} for {county.title()} completed with status: {job_status["status"]}')
                if job_status['status'] == 'FAILED':
                    failed_jobs_count += 1
                    failed_jobs.append({'county': county, 'jobId': job_id, 'status': job_status['status'], 'error': job_status.get('message', 'No error message')})
            else:
                print(f'Job {job_id} for {county} not found or failed.')
            # break
        print(f'Checked {len(processed_jobs)} jobs. {failed_jobs_count} jobs failed.')
        if failed_jobs:
            print(f'Failed jobs: {failed_jobs}')
            with open('../output/failed_jobs.json', 'w') as f:
                json.dump(failed_jobs, f, indent=4)
        else:
            print('No failed jobs found.')

if __name__ == '__main__':
    main('check_jobs')
    # main('upload')