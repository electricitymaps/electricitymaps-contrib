import numpy as np

from electricitymap.contrib.config import ZONE_NEIGHBOURS, ZONES_CONFIG, ZoneKey


def build_adjacency_matrix(zones_config: dict, zones_neighbours) -> np.ndarray:
    n_zones = len(zones_config)
    idx_to_zone_key = {
        idx: zone_key for idx, zone_key in enumerate(zones_config.keys())
    }
    zone_key_to_idx = {zone_key: idx for idx, zone_key in idx_to_zone_key.items()}

    adjacency_matrix = np.zeros((n_zones, n_zones))
    for zone_key, neighbours in zones_neighbours.items():
        for neighbour in neighbours:
            adjacency_matrix[zone_key_to_idx[zone_key], zone_key_to_idx[neighbour]] = 1
            adjacency_matrix[zone_key_to_idx[neighbour], zone_key_to_idx[zone_key]] = 1
    return adjacency_matrix


# Cluster
def get_clusters(adjacency_matrix: np.ndarray) -> np.ndarray:
    from sklearn.cluster import DBSCAN

    idx_all_zeros = np.where(~adjacency_matrix.any(axis=1))[0]
    idx_non_zeros = np.where(adjacency_matrix.any(axis=1))[0]
    # remove rows and columns of all zeros
    non_zeros_adjacency_matrix = np.delete(adjacency_matrix, idx_all_zeros, axis=0)
    non_zeros_adjacency_matrix = np.delete(
        non_zeros_adjacency_matrix, idx_all_zeros, axis=1
    )

    distance_matrix = 1 - non_zeros_adjacency_matrix
    dbscan = DBSCAN(eps=0.5, min_samples=1, metric="precomputed")
    clusters = dbscan.fit_predict(distance_matrix)

    all_clusters = -1 * np.ones(adjacency_matrix.shape[0])
    all_clusters[idx_non_zeros] = clusters
    return all_clusters


# Connected components
def get_connected_components(adjacency_matrix: np.ndarray) -> np.ndarray:
    from collections import defaultdict

    n = adjacency_matrix.shape[0]
    # From adjacency matrix, get list of edges [[v_i, v_j], ...]
    edges = []
    for i in range(adjacency_matrix.shape[0]):
        for j in range(i, adjacency_matrix.shape[1]):
            if adjacency_matrix[i, j] == 1:
                edges.append([i, j])

    def merge(parent: list[int], x: int) -> int:
        if parent[x] == x:
            return x
        return merge(parent, parent[x])

    parent = [i for i in range(n)]

    for e in edges:
        parent[merge(parent, e[0])] = merge(parent, e[1])

    for i in range(n):
        parent[i] = merge(parent, parent[i])

    connected_components = defaultdict(list)
    for i in range(n):
        connected_components[parent[i]].append(i)

    all_connected_components = -1 * np.ones(n)
    ct = 0
    for i, components in enumerate(connected_components.values()):
        # If there is a single element, it is not a connected component
        if len(components) > 1:
            for component in components:
                all_connected_components[component] = ct
            ct += 1
    return all_connected_components


def extract_connected_zones(
    zone_key: ZoneKey, zones_config: dict, connected_components: np.ndarray
) -> list[ZoneKey]:
    """
    Get all zones part of a same set of connected components.
    """
    _zone_keys = list(zones_config.keys())
    idx_zone_key = _zone_keys.index(zone_key)
    idx_cluster = connected_components[idx_zone_key]
    if idx_cluster == -1:
        return [zone_key]
    else:
        return [
            _zone_keys[idx]
            for idx, cluster in enumerate(connected_components)
            if cluster == idx_cluster
        ]


def get_all_connected_zones(zone_key: ZoneKey) -> list[ZoneKey]:
    """
    Get all zones part of a same set of connected components.
    """
    adjacency_matrix = build_adjacency_matrix(ZONES_CONFIG, ZONE_NEIGHBOURS)
    connected_components = get_connected_components(adjacency_matrix)
    return extract_connected_zones(zone_key, ZONES_CONFIG, connected_components)


def visualise() -> None:
    from time import time

    import geopandas as gpd
    import matplotlib.pyplot as plt
    import pandas as pd
    from matplotlib.colors import ListedColormap

    s_time = time()
    adjacency_matrix = build_adjacency_matrix(ZONES_CONFIG, ZONE_NEIGHBOURS)
    print(f"Time to build adjacency matrix: {time() - s_time:.2f}s")

    # s_time = time()
    # all_clusters = get_clusters(adjacency_matrix)
    # print(f"Time to cluster: {time() - s_time:.2f}s")

    s_time = time()
    all_connected_components = get_connected_components(adjacency_matrix)
    print(f"Time to get connected components: {time() - s_time:.2f}s")

    # ONLY FOR VISUALIZATION / DEMO
    def find_bounding_box_center(bounding_box: list[list[float]]) -> tuple[float]:
        """
        Find the center of a bounding box.
        Bounding box is [[min_lon, min_lat], [max_lon, max_lat]
        """
        return (
            (bounding_box[0][1] + bounding_box[1][1]) / 2,
            (bounding_box[0][0] + bounding_box[1][0]) / 2,
        )

    colours = [
        "grey",
        "#8b4513",
        "#006400",
        "#4682b4",
        "#4b0082",
        "#ff0000",
        "#ffd700",
        "#00ff7f",
        "#00ffff",
        "#0000ff",
        "#ffe4b5",
        "#ff69b4",
    ]
    # Make colour palette for clusters
    cmap = ListedColormap(colours)

    zones = pd.DataFrame(
        [
            {
                "zone_key": zone_key,
                "latitude": np.nan,
                "longitude": np.nan,
                "cluster": np.nan,
            }
            for zone_key in ZONES_CONFIG.keys()
        ]
    )
    zones = zones.set_index("zone_key")
    for i, zone_key in enumerate(ZONES_CONFIG.keys()):
        bb = ZONES_CONFIG[zone_key].get("bounding_box")
        if bb:
            lat, lon = find_bounding_box_center(bb)
            zones.loc[zone_key, "latitude"] = lat
            zones.loc[zone_key, "longitude"] = lon
        zones.loc[zone_key, "cluster"] = all_connected_components[i]
    zones.cluster = zones.cluster.astype(int)
    # order by cluster asc - to make sure that non clustered zones will be overwritten by clustered ones
    zones = zones.sort_values(by="cluster")

    fig, ax = plt.subplots(figsize=(20, 10))
    countries = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    countries.plot(color="lightgrey", ax=ax)
    # Also plot edges between zones with neighbourhoods
    for zone_key, neighbours in ZONE_NEIGHBOURS.items():
        for neighbour in neighbours:
            if zone_key < neighbour:
                ax.plot(
                    [
                        zones.loc[zone_key, "longitude"],
                        zones.loc[neighbour, "longitude"],
                    ],
                    [zones.loc[zone_key, "latitude"], zones.loc[neighbour, "latitude"]],
                    color="black",
                    alpha=0.5,
                )

    zones.plot(
        x="longitude",
        y="latitude",
        kind="scatter",
        c="cluster",
        colormap=cmap,
        title=f"Zones clustering",
        ax=ax,
    )
    for idx, row in zones.iterrows():
        ax.annotate(idx, (row["longitude"], row["latitude"]))
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    visualise()
