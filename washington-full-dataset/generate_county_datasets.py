import sys
import json
import asyncio
import os
# from osm-convert import Formatter
# from osm-convert import Formatter

from osm_osw_reformatter import Formatter



def download_osm_file(file_path, dataset_name):
    working_dir = os.path.join("../output/county-datasets", dataset_name)
    f = Formatter(workdir=working_dir, file_path=file_path)
    asyncio.run(f.osm2osw())
    

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
    
    # Loop through the files and process them
    for osmfile in files_to_process:
        # Get the name of the file without the extension
        dataset_name = os.path.basename(osmfile).split('.')[0]
        print("Processing %s" % osmfile)
        download_osm_file(osmfile, dataset_name)
    
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python %s <osmfile>" % sys.argv[0])
        sys.exit(-1)
    sys.exit(main(sys.argv[1]))