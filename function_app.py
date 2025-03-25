import azure.functions as func
import logging
from azure.storage.blob import BlobServiceClient
import subprocess
import os
from datetime import datetime
from pathlib import Path
import logging
import time


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

def dump_database(database_name):
    logging.info(f"Starting backup of database {database_name}")
    password = os.getenv('PGPASSWORD')
    host_name = os.getenv('PGHOST')
    user_name = os.getenv('PGUSER')
    pattern = 'cron.job*'

    time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_file = database_name + str(time_stamp) + ".dump"

    database_bck_path = os.path.join("/tmp", backup_file)
    env = os.environ.copy()
    env["PGPASSWORD"] = password

    command = f'pg_dump -Fc -v --host={host_name} --username={user_name} --dbname={database_name} -f {database_bck_path}'
    cmd = ['pg_dump', 
           '-h', host_name,
           '-U', user_name,
           '-F','c', '-v', 
           '-f', database_bck_path]
    try:
        proc = subprocess.run(cmd, check=True, env=env)
        # print the output
        print(proc.stdout)
        # proc.wait()
        logging.info(f"Ended backup of database {database_name}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error {e} while running the backup of {database_name}")
    except Exception as e:
        logging.error(f"Error {e} while running the backup of {database_name}")
    return database_bck_path


def upload_backup_container(container_name, upload_file_path):
    blob_service_client = BlobServiceClient.from_connection_string(
        os.getenv('STORAGE_CONNECTION_STRING'))

    blob_client = blob_service_client.get_blob_client(
        container=container_name, blob=Path(upload_file_path).name)
    try:
        with open(upload_file_path, "rb") as data:
            blob_client.upload_blob(data, blob_type="BlockBlob")
        logging.info(
            f"Uploaded backup to {container_name} as blob {Path(upload_file_path).name}")
    except Exception as error:
        logging.error(f"Error: {error} while uploading the file ")
    finally:
        os.remove(upload_file_path)


def check_env_strings():
    storage_string = os.getenv('STORAGE_CONNECTION_STRING')
    if storage_string is None:
        logging.error("STORAGE_CONNECTION_STRING is not set")
        return False
    pg_host = os.getenv('PGHOST')
    if pg_host is None:
        logging.error("PGHOST is not set")
        return False
    pg_user = os.getenv('PGUSER')
    if pg_user is None:
        logging.error("PGUSER is not set")
        return False
    pg_password = os.getenv('PGPASSWORD')
    if pg_password is None:
        logging.error("PGPASSWORD is not set")
        return False
    return True

@app.route(route="waposmdbbkup")
def waposmdbbkup(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    if not check_env_strings():
        return func.HttpResponse(
            "Environment variables are not set properly",
            status_code=500
        )
    
    container_name = 'waposmdbbkup'
    logging.info(f"Starting backup of database proviso-posm-db to container {container_name}")
    backup_path = dump_database('proviso-posm-db')
    upload_backup_container(container_name, backup_path)

    return func.HttpResponse(f"Hello, This HTTP triggered function executed successfully.")