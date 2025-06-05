from osm_osw_reformatter import Formatter
import asyncio
import osmium
from shapely.geometry import LineString, Point
import json
from geojson import Feature, FeatureCollection
from osm_osw_reformatter import Response

import os
def start_converstion():
    working_dir = '../output/county-datasets/washington'
    file_path = '../output/complete.pbf'
    f = Formatter(workdir=working_dir, file_path=file_path)
    result = asyncio.run(f.osm2osw())
    print(result)



class OSWHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        # self.output_file = output_file
        self.nodes = {}
        self.ways = []
        

    def node(self, n):
        node_point = Point(n.location.lon, n.location.lat)  # Create a Shapely Point object
        node_data = {
            'id': str(n.id),
            'geometry': node_point,
            'tags': dict(n.tags)
        }
        self.nodes[str(n.id)] = node_data
         

    def way(self, w):
        way_nodes = w.nodes
        way_points = []
        if len(way_nodes) < 2:
            print(f'Way {w.id} has less than 2 nodes, skipping.')
            return
        for n in way_nodes:
            geometry = self.nodes.get(str(n.ref))
            if geometry:
                way_points.append(geometry['geometry'])
            else:
                print(f'Node {n.ref} not found in nodes dictionary.')
        way_geometry = LineString(way_points)
        u_id = str(w.nodes[0].ref)
        v_id = str(w.nodes[-1].ref)
        way_data = {
            'id': str(w.id),
            'geometry': way_geometry,
            'tags': dict(w.tags),
            'u_id': u_id,
            'v_id': v_id
        }
        self.ways.append(way_data)
        
    def show_results(self):
        print(f'Processed {len(self.nodes)} nodes and {len(self.ways)} ways.')
        first_coords = self.ways[0]['geometry'].coords  # Access the geometry of the first way to trigger its creation
        print(f'First way coordinates: {first_coords}')
        for coord in first_coords:
            print(f'Coordinate: {coord}')
    def export_results(self,output_dir,dataset_name:str = 'final'):
        # Check if output_dir exists, if not create it
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        nodes_file = os.path.join(output_dir, dataset_name+'.nodes.geojson')
        ways_file = os.path.join(output_dir, dataset_name+'.edges.geojson')
        nodes_feature_collection = FeatureCollection([])
        ways_feature_collection = FeatureCollection([])
        for i, node in enumerate(self.nodes.values()):
            properties = {}
            for key, value in node['tags'].items():
                properties[key] = value
            properties['_id'] = str(node['id'])
            node_feature = Feature(geometry=node['geometry'], properties=properties)
            nodes_feature_collection.features.append(node_feature)
        with open(nodes_file, 'w') as f:
            nodes_feature_collection['$schema'] = "https://sidewalks.washington.edu/opensidewalks/0.2/schema.json"
            nodes_feature_collection_json = json.dumps(nodes_feature_collection)
            f.write(nodes_feature_collection_json)
         
        for i, way in enumerate(self.ways):
            properties = {}
            for key, value in way['tags'].items():
                properties[key] = value
            points = []
            for point in way['geometry'].coords:
                points.append([point[0], point[1]])
            properties['_id'] = str(way['id'])
            properties['_u_id'] = str(way['u_id'])
            properties['_v_id'] = str(way['v_id'])
            properties = self.transform_tags(properties)
            properties = self.remove_unnecessary_tags(properties)
            way_feature = Feature(geometry=LineString(points), properties=properties)
            ways_feature_collection.features.append(way_feature)
        with open(ways_file, 'w') as f:
            ways_feature_collection['$schema'] = "https://sidewalks.washington.edu/opensidewalks/0.2/schema.json"
            ways_feature_collection_json = json.dumps(ways_feature_collection)
            f.write(ways_feature_collection_json)
    def transform_tags(self,tags):
        if tags.get('crossing'):
            crossing_type = tags['crossing']
            tags['crossing:markings'] = self.crossing_to_crossing_markings(crossing_type)
            # remove the crossing tag
            del tags['crossing']
        if tags.get('width'):
            # convert to float with two decimal places
            try:
                tags['width'] = float(tags['width'])
                tags['width'] = round(tags['width'], 2)
            except ValueError:
                tags['width'] = 0.0
        return tags

    def crossing_to_crossing_markings(self, crossing_type):
        if crossing_type == 'marked':
            return 'yes'
        elif crossing_type == 'unmarked':
            return 'no'
        else:
            return 'no' 
    def remove_unnecessary_tags(self,tags):
        unnecessary_way_tags = ['layer','tunnel', 'bridge', 'tactile_paving', 'wheelchair', 'crossing:island',
                              'barrier', 'kerb', 'covered', 'bicycle','crossing:signals']
        tags_to_remove = []
        for key, value in tags.items():
            if key in unnecessary_way_tags:
                tags_to_remove.append(key)
        for tag_key in tags_to_remove:
            del tags[tag_key]
        return tags    
    # def apply_surface_transform(self,surface_type):
    #     surface_tag = next((tag for tag in self.tags if tag.key == 'surface'), None)
    #     if surface_tag and surface_tag.value in ['ground']:
    #         self.tags.remove(surface_tag)
    #         self.tags.append(Tag('surface', 'unpaved'))   

             

class OsmiumOSWConverter:
    def __init__(self, workdir=str, file_path=str):
        self.working_dir = workdir
        self.file_path = file_path
        self.handler = OSWHandler()
    def convert(self):
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)
        self.handler.apply_file(self.file_path)
        dataset_name = os.path.splitext(os.path.basename(self.file_path))[0]
        # check for suffix .osm.pbf and remove it
        dataset_name = dataset_name.replace('.osm.pbf', '')
        print(f'Processing file: {self.file_path}')
        print(f'Output will be saved in: {self.working_dir}')
        self.handler.export_results(self.working_dir, dataset_name='final.'+dataset_name)
        output_dir = self.working_dir
        print(f'Conversion completed. Results saved in {output_dir}')
        # Get the list of files from output directory
        files = os.listdir(output_dir)
        print(f'Files in output directory: {files}')
        # return a tuple with generated files
        files = [os.path.join(output_dir, file) for file in files if file.endswith('.geojson')]
        print(f'Generated files: {files}')
        resp = Response(status=True, generated_files=files)
        return resp

        
def main():
    handler = OSWHandler()
    input_file = '../output/benton.osm.pbf'
    handler.apply_file(input_file)
    handler.show_results()
    handler.export_results('../output/county-datasets/benton', dataset_name='benton')

if __name__ == '__main__':
    main()
    # start_converstion()