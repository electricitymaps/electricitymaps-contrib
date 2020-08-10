import copy
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx
import random


ZONES_FILE = 'zones.json'
EXCHANGES_FILE = 'exchanges.json'
colours = [
    '#990000',
    # '#ffffff',
    # '##000000',
    '#2F3EEA',
    '#1FD082',
    '#030F4F',
    '#F6D04D',
    '#FC7634',
    '#F7BBB1',
    '#DADADA',
    '#E83F48',
    '#008835',
    '#79238E'
]

with open(ZONES_FILE, 'r') as f:
    zones = json.loads(f.read())

with open(EXCHANGES_FILE, 'r') as f:
    exchanges = json.loads(f.read())


zone_names = zones.keys()
zone_name_exchanges = exchanges.keys()
zone_names_without_bd = set()

G = nx.Graph()
zone_positions = {}
label_positions = {}

for zone_name in zone_names:
    # Create positions for zones by taking middle of bounding boxes
    # pos must be { "ZONE_KEY": [x, y] }
    try:
        bounding_box = zones[zone_name]["bounding_box"]
        zone_positions[zone_name] = [
            (bounding_box[0][0] + bounding_box[1][0]) / 2,
            (bounding_box[0][1] + bounding_box[1][1]) / 2,
        ]
        label_positions[zone_name] = [
            (bounding_box[0][0] + bounding_box[1][0]) / 2 + 1,
            (bounding_box[0][1] + bounding_box[1][1]) / 2 + 1,
        ]
        G.add_node(zone_name)
    except KeyError:
        # Ignore zones that don't have bounding boxe
        print(f"Zone {zone_name} does not have a defined bounding box")
        zone_names_without_bd.add(zone_name)
        pass

# Cluster information is very useful in itself!
zone_clusters = {}  # cluster_index: {zone_names}
zone_cluster_idx = {}  # zone_name: cluster index
cluster_idx = 0

for zone_name_exchange in zone_name_exchanges:
    zone_name_1, zone_name_2 = zone_name_exchange.split('->')
    if ((zone_name_1 in zone_names)
        & (zone_name_1 not in zone_names_without_bd)
        & (zone_name_2 in zone_names)
        & (zone_name_2 not in zone_names_without_bd)):
            G.add_edge(*(zone_name_1, zone_name_2))
            # none of the zones is in a cluster
            if ((zone_name_1 not in zone_cluster_idx.keys())
              & (zone_name_2 not in zone_cluster_idx.keys())):
                cluster = {zone_name_1, zone_name_2}
                zone_clusters[cluster_idx] = cluster
                zone_cluster_idx[zone_name_1] = cluster_idx
                zone_cluster_idx[zone_name_2] = cluster_idx
                cluster_idx += 1
            # zone 1 is in a cluster
            elif ((zone_name_1 in zone_cluster_idx.keys())
              & (zone_name_2 not in zone_cluster_idx.keys())):
                cid = zone_cluster_idx[zone_name_1]
                new_cluster = copy.deepcopy(zone_clusters[cid])
                new_cluster.add(zone_name_2)
                zone_clusters[cid] = new_cluster
                zone_cluster_idx[zone_name_2] = cid
            # zone 2 is in a cluster
            elif ((zone_name_1 not in zone_cluster_idx.keys())
              & (zone_name_2 in zone_cluster_idx.keys())):
                cid = zone_cluster_idx[zone_name_2]
                new_cluster = copy.deepcopy(zone_clusters[cid])
                new_cluster.add(zone_name_1)
                zone_clusters[cid] = new_cluster
                zone_cluster_idx[zone_name_1] = cid
            # both are in clusters
            elif ((zone_name_1 in zone_cluster_idx.keys())
              & (zone_name_2 in zone_cluster_idx.keys())):
                cid_1 = zone_cluster_idx[zone_name_1]
                cid_2 = zone_cluster_idx[zone_name_2]
                if (cid_1 == cid_2):
                    continue
                cluster_1 = copy.deepcopy(zone_clusters[cid_1])
                cluster_2 = copy.deepcopy(zone_clusters[cid_2])
                new_cluster = cluster_1.union(cluster_2)
                for zone_name in cluster_2:
                    zone_cluster_idx[zone_name] = cid_1
                zone_clusters[cid_1] = new_cluster
                del zone_clusters[cid_2]

cluster_colours = {
    cluster_idx: random.choice(colours) for cluster_idx in zone_clusters.keys()
}
node_colours = []
for zone_name in zone_positions.keys():
    if zone_name in zone_cluster_idx.keys():
        node_colours.append(cluster_colours[zone_cluster_idx[zone_name]])
    else:
        node_colours.append("black")


nx.draw(
    G,
    zone_positions,
    alpha=0.8,
    node_color=node_colours,
    node_size=10,
)
nx.draw_networkx_labels(
    G,
    label_positions,
    {zone_name: zone_name for zone_name in label_positions.keys()},
    font_size=6
)
plt.show()
