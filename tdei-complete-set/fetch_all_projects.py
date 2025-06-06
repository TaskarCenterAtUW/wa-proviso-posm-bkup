
import requests
from dotenv import load_dotenv
import os
from tqdm import tqdm
load_dotenv()
import pandas as pd
import json
import io

class TDEIDatasetDownloader : 

    base_url = 'https://api.tdei.us'
    datasets_path = '/api/v1/datasets'
    auth_path = '/api/v1/authenticate'
    access_token = None

    # username = os.getenv('TDEI_USERNAME')
    # password = os.getenv('TDEI_PASSWORD')
    # project_group_id = '1dd7c38e-c7a6-4e3a-be8b-379f823a7ad7' # GS_WSP_PG

    def get_access_token(self, username: str, password: str):
        url = self.base_url + self.auth_path
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
    
    def fetch_quality_metric(self, dataset_id):
        try:
            url = self.base_url+'/api/v1/osw/quality-metric/tag/'+dataset_id
            headers = {'Authorization': f'Bearer {self.access_token}'}
            tag_quality_payload = [
            {
                "entity_type": "Sidewalk",
                "tags": [
                    "surface",
                    "width",
                    "incline",
                    "length",
                    "description",
                    "name",
                    "foot"
                ]
            }
        ]
            tag_quality_bytes = json.dumps(tag_quality_payload).encode('utf-8')
            files = {"file": ('tag_quality_payload.json', io.BytesIO(tag_quality_bytes), 'application/json')}
            data = {'tdei_dataset_id': dataset_id}
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            print(f"Response status for {dataset_id}: {response.status_code}")
            print(f"Response JSON for {dataset_id}: {response.json()}")
            result = response.json()[0]
            metrics = result.get('metric_details', {})
            print(f"Extracted metrics for {dataset_id}: {metrics}")

            return metrics
        except Exception as e:
            print(f"[ERROR] Quality metric for {dataset_id}: {e}")
            return {}


    def search_datasets(self, query_params):
        if not self.access_token:
            print(f'No access token found. Please authenticate first.')
            return []
        # query_params = {
        #     'page_no': 1,
        #     'page_size': 50,
        #     'tdei_project_group_id':project_group_id,
        #     'data_type':'osw',
        #     'sort_field':'uploaded_timestamp',
        #     'sort_order':'asc'
        # }
        datasets = []
        datasets_url = self.base_url + self.datasets_path
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
                    dataset_area = data['metadata']['dataset_detail'].get('dataset_area')
                    if dataset_area and 'features' in dataset_area:
                        features = dataset_area.get('features', [])
                    else:
                        features = []

                feature = features[0] if features else {}

                dataset_id = data['tdei_dataset_id']
                metrics = self.fetch_quality_metric(dataset_id)
    
                datasets.append({
                'name': data['metadata']['dataset_detail']['name'],
                'upload_date': data['uploaded_timestamp'],
                'version': data['metadata']['dataset_detail']['version'],
                'service': data['service']['name'],
                'project_group': data['project_group']['name'],
                'tdei_dataset_id': data['tdei_dataset_id'],
                'custom_metadata': data['metadata']['dataset_detail'].get('custom_metadata', {}),
                'geometry': feature.get('geometry', {}) if feature else {},
                'surface_percentage': metrics.get('surface_percentage'),
                'width_percentage': metrics.get('width_percentage'),
                'incline_percentage': metrics.get('incline_percentage'),
                })

                page_no += 1
                query_params['page_no'] = page_no
                response = requests.get(datasets_url,params=query_params, headers=headers)
            else:
                for data in response.json():
                    feature = {}
                    features = data['metadata']['dataset_detail']['dataset_area'].get('features', [])
                    if len(features) > 0:
                        feature = features[0]
                    datasets.append({'name':data['metadata']['dataset_detail']['name'],
                    'upload_date':data['uploaded_timestamp'],
                    'version':data['metadata']['dataset_detail']['version'],
                    'tdei_dataset_id':data['tdei_dataset_id'],
                    'custom_metadata':data['metadata']['dataset_detail'].get('custom_metadata', {}),
                    'geometry': feature.get('geometry', {}) if feature else {}})
                print(f'Fetching page {page_no}')
                break

        return datasets
    
    def get_latest_datasets(self, query_params):
        print(f'Fetching all the datasets')
        datasets = self.search_datasets(query_params)
        print(f' Found {len(datasets)} datasets')
        if not datasets:
            print(f'No datasets found.')
            return pd.DataFrame()
        df = pd.DataFrame(datasets)
        df_sorted = df.sort_values(by=['name', 'version'], ascending=[True, False])
        df_deduplicated = df_sorted.groupby('name').first().reset_index()
        return df_deduplicated
    
    def download_dataset(self, dataset_id, download_folder:str='./downloads'):
        if not self.access_token:
            print(f'No access token found. Please authenticate first.')
            return []
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        # api/v1/osw/d3134df9-be46-4453-876c-ca77fd98e89e?format=osw&file_version=latest
        download_url = f'{self.base_url}/api/v1/osw/{dataset_id}?format=osw&file_version=latest'
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        response = requests.get(download_url, headers=headers, stream=True)
        download_path = os.path.join(download_folder, f'{dataset_id}.zip')
        if response.status_code == 200:
            with open(download_path, 'wb') as f:
                for chunk in tqdm(response.iter_content(chunk_size=2048), desc=f'Downloading {dataset_id}'):
                    f.write(chunk)
            print(f'Downloaded {dataset_id}')
        else:
            print(f'Failed to download {dataset_id}')


if __name__ == '__main__':
    downloader = TDEIDatasetDownloader()
    username = os.getenv('TDEI_USERNAME')
    password = os.getenv('TDEI_PASSWORD')
    access_token = downloader.get_access_token(username, password)
    project_group_id = '0eace285-430b-4f3e-bd76-d102a2c5385c' #TCAT_WSP_PG
    query_params = {
        'page_no': 1,
        'page_size': 50,
        'tdei_project_group_id':project_group_id,
        'data_type':'osw',
        'sort_field':'uploaded_timestamp',
        'sort_order':'asc',
        'status':'Publish',
        'tdei_service_id':'f24b624c-8253-48d4-ae92-34e4395213e1'
    }
    datasets = downloader.get_latest_datasets(query_params)
    for index, row in tqdm(datasets.iterrows(), total=len(datasets), desc='Downloading datasets'):
        dataset_id = row['tdei_dataset_id']
        downloader.download_dataset(dataset_id)
    datasets.to_json('tdei_datasets.json', orient='records', indent=4)
    '''
    Command to generate GeoJSON from the dataset JSON file:
    jq '{
  type: "FeatureCollection",
  features: map({
    type: "Feature",
    geometry: .geometry,
    properties: (
      del(.geometry) 
      | .custom_metadata as $custom
      | del(.custom_metadata)
      | . + $custom
    )
  })
}' tdei_datasets.json > washington_dataset_boundaries.geojson
'''
     