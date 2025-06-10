import json
import requests
import os
import time
from mc_upload_report import MCUploadReport
class MissonControlService:
    def __init__(self, project_group_id: str, service_id: str):
        self.project_group_id = project_group_id
        self.service_id = service_id
        self.base_url = "https://wa-proviso-api-dev.azurewebsites.net"
        pass
    
    def initiate_dataset_upload_job(self, dataset_name: str, working_dir:str, access_token: str,mc_project_id: str,environment: str = "prod",):
        # url = https://wa-proviso-api-dev.azurewebsites.net/projects/6848071f7fe063e3230cab6b/upload-tdei-dataset
        '''
                Payload sample:
                {
        "boundary": {
            "type": "Feature",
            "properties": {
            "name": "GS Asotin County",
            "id": "6848071f7fe063e3230cab6b",
            "tdei_service_id": "d1199d1a-495b-43a0-b7cd-1f941a657356",
            "tdei_pg_id": "1dd7c38e-c7a6-4e3a-be8b-379f823a7ad7"
            },
            "geometry": {}
        },
        "metadata": {},
        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICIxeEpjaktNdk9RcWQtXzZUMGhZN0JsS2lRVXd0dlFIbHd1M2hSTjNLRm1vIn0.eyJleHAiOjE3NDk2MTM2NjQsImlhdCI6MTc0OTUyNzI2NCwianRpIjoiNWZmYjZhMWEtNGE0My00MTZjLWI1MzMtNWU5MTZmYmRiNjY1IiwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50LnRkZWkudXMvcmVhbG1zL3RkZWkiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiNWIyZjI4ZTYtMzRhMC00MzU4LTk2NGEtZjZiMTdlMDE5ZjNhIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoidGRlaS1nYXRld2F5Iiwic2lkIjoiODE1NzdhYWQtNDJlNS00OTM0LWE4ODctMjU2YmJkZGIyNWQ0IiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyIiLCIqIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsImRlZmF1bHQtcm9sZXMtdGRlaSIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJlbWFpbCBwcm9maWxlIG9wZW5pZCIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiTmFyZXNoIEt1bWFyIEt1bWFyIiwicHJlZmVycmVkX3VzZXJuYW1lIjoibmFyZXNoZEBnYXVzc2lhbnNvbHV0aW9ucy5jb20iLCJnaXZlbl9uYW1lIjoiTmFyZXNoIEt1bWFyIiwiZmFtaWx5X25hbWUiOiJLdW1hciIsImVtYWlsIjoibmFyZXNoZEBnYXVzc2lhbnNvbHV0aW9ucy5jb20ifQ.cCN7ZCBWCQvitefquwZfCmnIFxgtvPtKMjfQhN096xd1nWGEJXqQczQyniYv184i5ogFSE-kfIff79luYbUr1gASxy0svF5ZIPT6xeM6EJZE06E_xKNZvl7orpIGnJvKV3ybn2HrlmSmFJFdD-jj7HSStEna6FdaqouqlU7AvThcx3tyfFLPtxKUamggBz0vLsgwy-wKoeknZwugeQWsq0yS_ZCNIds7yAB6Pm8m_4wPFd-jOhFzjek_2EAuz0IlZ0PsX8VOu8mGqlQ-wHHGcEQCe9ZSPOEoIiiJh-GOdGpvK_33sepT-JatY5pKBY3eLEeEzHyGOMBp1-TMyHhTyg",
        "environment": "prod"
        }       
    '''
     # Go through the working_dir and find boundary file (name ends with boundary.geojson)
        boundary_file_path = None
        for file in os.listdir(working_dir):
            if file.endswith("boundary.geojson"):
                boundary_file_path = os.path.join(working_dir, file)
                break
        if not boundary_file_path:
            raise FileNotFoundError("Boundary file not found in the working directory.")
        for file in os.listdir(working_dir): 
            if file.endswith("metadata.json"):
                metadata_file_path = os.path.join(working_dir, file)
                break
        if not metadata_file_path:
            raise FileNotFoundError("Metadata file not found in the working directory.")
        # Load the boundary file
        with open(boundary_file_path, 'r') as f:
            boundary_data = json.load(f)
        boundary_payload = boundary_data.get('features', [])[0]
        if not boundary_payload:
            raise ValueError("No features found in the boundary file.")
        # Add the name, id, tdei_service_id, and tdei_pg_id to the boundary payload
        boundary_payload['properties']['name'] = dataset_name
        boundary_payload['properties']['id'] = mc_project_id
        boundary_payload['properties']['tdei_service_id'] = self.service_id
        boundary_payload['properties']['tdei_pg_id'] = self.project_group_id
        # Load the metadata file
        with open(metadata_file_path, 'r') as f:
            metadata = json.load(f)
        # Prepare the payload
        payload = {
            "boundary": boundary_payload,
            "metadata": metadata,
            "access_token": access_token,
            "environment": environment
        }
        # Make the POST request
        url = f"{self.base_url}/projects/{mc_project_id}/upload-tdei-dataset"
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            flow_id = response.json().get('flow_id')
            if not flow_id:
                raise ValueError("Flow ID not found in the response.")
            return flow_id
        else:
            raise Exception(f"Failed to initiate dataset upload job: {response.status_code} - {response.text}")

    def check_job_status(self,project_id:str, flow_id: str):
        """
        Check the status of a job using its flow ID.
        """
        url = f"{self.base_url}/projects/{project_id}/jobs"
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            total_jobs = response.json().get('total', 0)
            total_data = response.json().get('data', [])
            # Get the job with the specified flow_id
            job = next((job for job in total_data if job.get('jobId') == flow_id), None)
            if not job:
                raise ValueError(f"Job with flow_id {flow_id} not found.")
            return job
        else:
            raise Exception(f"Failed to check job status: {response.status_code} - {response.text}")
        
    def get_job_result(self, project_id: str, flow_id: str):
        # Check the status of the job first
        start_time = time.time()
        while True:
            job_status = self.check_job_status(project_id, flow_id)
            response  = job_status.get('response', {})
            report_url = response.get('report_url',None)
            if report_url is None:
                print(f"Job {flow_id} is not finished yet. Current state: {job_status.get('state')}")
                time_since_start = time.time() - start_time
                # If the time since the start is more than 30 minutes, raise an error
                if time_since_start > 1800:  # 30 minutes
                    raise TimeoutError(f"Job {flow_id} is taking too long to finish. Current state: {job_status.get('state')}")
                time.sleep(15)
            else:
                print(f"Job {flow_id} is finished. Retrieving results...")
                # If the job is finished, retrieve the results
                # report_url = job_status.get('report_url')
                # Fetch the report URL
                if not report_url:
                    raise ValueError("Report URL not found in the job status.")
                report_response = requests.get(report_url)
                if report_response.status_code == 200:
                    upload_report_data = report_response.json()
                    # Create an instance of MCUploadReport
                    upload_report = MCUploadReport(upload_report_data)
                    # Check the status of the upload report
                    is_valid, status_message = upload_report.get_status()
                    if not is_valid:
                        raise ValueError(f"Upload report indicates an error: {status_message}")
                    
                    return upload_report.tdei_job_id
                else:
                    raise Exception(f"Failed to retrieve job results: {report_response.status_code} - {report_response.text}")

def main():
    # Example usage
    # project_group_id = "1dd7c38e-c7a6-4e3a-be8b-379f823a7ad7"
    # service_id = "d1199d1a-495b-43a0-b7cd-1f941a657356"
    # Stage creds
    project_group_id = "b8098696-7588-4278-beb8-a730d33a71cc"
    service_id = "739193fc-ce3b-4f12-9271-e21b26238209"

    service = MissonControlService(project_group_id=project_group_id, service_id=service_id)
    try:
        result = service.initiate_dataset_upload_job(
            dataset_name="GS Asotin County",
            working_dir="../output/county-datasets/asotin",
            access_token="eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI4bDNEZ2ZrSS03ejJNNFJkMXVIWEEtLWZzdTNsZUxwU2x3TG1JOGJ3RmlRIn0.eyJleHAiOjE3NDk2NTIwOTUsImlhdCI6MTc0OTU2NTY5NSwianRpIjoiNjMxNDk5NTQtNjI1Zi00ZjRmLWJiY2QtYmY1YjcyOGY4MTc0IiwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50LXN0YWdlLnRkZWkudXMvcmVhbG1zL3RkZWkiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiMzE3NmI2YjYtNjUyNC00YmZkLTg2ZWQtYzM4MDQ1ZGQ2OTlhIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoidGRlaS1nYXRld2F5Iiwic2lkIjoiMmJhMzI2MDAtMmQ3Yi00MWU0LWI5NTItYzVlZjYyNzU2NGMwIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyIiLCIqIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsImRlZmF1bHQtcm9sZXMtdGRlaSIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJlbWFpbCBwcm9maWxlIG9wZW5pZCIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiTmFyZXNoIEt1bWFyIiwicHJlZmVycmVkX3VzZXJuYW1lIjoibmFyZXNoZEBnYXVzc2lhbnNvbHV0aW9ucy5jb20iLCJnaXZlbl9uYW1lIjoiTmFyZXNoIEt1bWFyIiwiZW1haWwiOiJuYXJlc2hkQGdhdXNzaWFuc29sdXRpb25zLmNvbSJ9.eO396Ys2BUNI8RjanhDEzKxyTS7O5LXq1TNoySfuKRLB_j9GLMs5zjkedFe8YswU-VayICfcqhw0UAuvivboubIDy2AGMlAFca82mP0nhPJw89rxTgLlb7pP1Yjni2gr7HL9GZKzUjeCU1JlOPLuIDqsClQFUWtuQHd-WYKOIwRsP7GpmQKzDxQpu2eEJ9cnSiPlmHTACWsUDNB3X9rol-qWO5eULZSeOqCPgtpCOxXGpiqJOJTQmJY8sEq8aiDPV3zIvo5ACQ9-xiuR2imx3s4_5Ygi91r9tvl64qjkPiC0Sjc4I-RJWUwj5yTKpsJ5me69WJ6fvtSJcriZXC4VHQ",
            mc_project_id="6848071f7fe063e3230cab6b",
            environment="stage"  # Change to "prod" for production environment
        )
        print("Dataset upload job initiated successfully:", result)
        return result
    except Exception as e:
        print("Error:", e)

def check_job_status_example(jobId:str):
    project_group_id = "1dd7c38e-c7a6-4e3a-be8b-379f823a7ad7"
    service_id = "d1199d1a-495b-43a0-b7cd-1f941a657356"
    service = MissonControlService(project_group_id=project_group_id, service_id=service_id)
    try:
        job_id = service.get_job_result(project_id="6848071f7fe063e3230cab6b", flow_id=jobId)
        print("Job status:", job_id)
    except Exception as e:
        print("Error checking job status:", e)
if __name__ == "__main__":
    job_id = main()
    # job_id = '028d009e-82ca-4611-9219-6685886cfd23'
    check_job_status_example(job_id)
        

