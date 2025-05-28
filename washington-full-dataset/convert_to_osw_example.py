from osm_osw_reformatter import Formatter
import asyncio

working_dir = '../output/county-datasets/washington'
file_path = '../output/complete.pbf'
f = Formatter(workdir=working_dir, file_path=file_path)
result = asyncio.run(f.osm2osw())
print(result)