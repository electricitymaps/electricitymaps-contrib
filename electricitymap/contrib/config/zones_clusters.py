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
    # TODO test individual components
    adjacency_matrix = build_adjacency_matrix(ZONES_CONFIG, ZONE_NEIGHBOURS)
    connected_components = get_connected_components(adjacency_matrix)
    return extract_connected_zones(zone_key, ZONES_CONFIG, connected_components)
