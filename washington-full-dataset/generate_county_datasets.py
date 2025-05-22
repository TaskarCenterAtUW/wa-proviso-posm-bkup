import osmium
import sys
import json
import asyncio
# from osm-convert import Formatter
# from osm-convert import Formatter
geojsonfab = osmium.geom.GeoJSONFactory()
from osm_osw_reformatter import Formatter

class NodeHandler(osmium.SimpleHandler):
    def __init__(self):
        super(NodeHandler, self).__init__()
        self.nodes = []

    def node(self, n):
        self.nodes.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [n.location.lon, n.location.lat]
            },
            "properties": {
                "id": n.id,
                "tags": dict(n.tags)
            }
        })

class GeoJsonWriter(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()
        # write the Geojson header
        self.ways = []
        self.nodes = []

    def finish(self):
        # print(']}')
        pass

    def node(self, n):
        if n.tags:
            # self.print_object(geojsonfab.create_point(n), n.tags)
            self.nodes.append(geojsonfab.create_point(n))
            print(n.id)

    def way(self, w):
        if w.tags and not w.is_closed():
            # self.print_object(geojsonfab.create_linestring(w), w.tags)
            self.ways.append(geojsonfab.create_linestring(w))

    def area(self, a):
      pass

    

def main(osmfile):

    f = Formatter(workdir="../output/county-datasets", file_path=osmfile)
    asyncio.run(f.osm2osw())
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python %s <osmfile>" % sys.argv[0])
        sys.exit(-1)
    sys.exit(main(sys.argv[1]))