# To enable ssh & remote debugging on app service change the base image to the one below
# FROM mcr.microsoft.com/azure-functions/python:4-python3.10-appservice
FROM mcr.microsoft.com/azure-functions/python:4-python3.10

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true
RUN apt-get update && apt-get install -y postgresql-client
COPY requirements.txt /
RUN apt-get update && apt-get install -y postgresql-client
RUN pip install -r /requirements.txt

COPY . /home/site/wwwroot