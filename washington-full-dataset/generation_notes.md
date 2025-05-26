# Generating individual county datasets from Washington state data
- The available data for Washington state is downloaded into `output` folder as a `.pbf` file as `complete.pbf`
- The dataset needs to be divided into multiple smaller `.pbf` files based on the geometry of each county
- There are two files for each county
    - < countyname >.geojson - County Boundary file
    - dow-< countyname >.geojson - County Data boundary file
- County Boundary file is the boundary of the actual jurisdiction
- County Data boundary file is the shape of the actual area considered for data collection within the county.
- The working directory for generating the files is `washington-full-dataset`
- `generate_config_file.py` is used to create a config file used for `osmium` to extract the data for each county
- `counties-config.json` is the config file to be used for generating individual `.pbf` files.
- Run the command `osmium extract -c counties-config.json ../output/complete.pbf` to generate individual `.pbf` files
- The resulting `.pbf` files are generated in the `output` folder
- Run `generate_county_datasets.py` like
    `python generate_county_datasets.py ../output/` 
- This script does the following:
    - Converts the `.pbf` file into osw records generating `edges` and `nodes` file
    - Generates the `metadata.json` file for each pbf file.
        - Metadata dataset boundary will be the County Data boundary file
        - Metadata custom_data['area'] will be the County Boundary file
        - Metadata version will be picked from GS_WSP_PG with service Proviso_Unions and same dataset name. The latest version is pulled and 0.01 is added to it
        - If there is no existing metadata, 1.0 is added as default version
        - Zips the edges and nodes files and makes it ready for upload

- At the end of the above script, we have individual folders with datasets and metadata ready
- Use `tdei_service.py` to upload the dataset to the TDEI system
- `python tdei_service.py`
- The script uploads the datasets to GS_WSP_PG production project group under service Proviso_Unions
- The jobID and county name are stored in `outputs/processed_jobs.json` file.

## Environment variables
- TDEI_USERNAME = username for TDEI System
- TDEI_PASSWORD = password for TDEI System
- TDEI_SERVICE_ID = service ID for looking up(searching) and uploading

 