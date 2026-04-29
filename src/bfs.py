import sys
from .map_model import Map, ZoneType


def check_solvability(map_obj: Map) -> bool:
    """Check if the map has at least one valid path from start to end.

    Args:
        map_obj: The map containing zones, connections, and drone config.

    Returns:
        True if at least one valid path exists, False otherwise.
    """
    paths: list[list[str]] = create_paths(map_obj, 1, True)
    return bool(paths)


def create_paths(map_obj: Map,
                 no: int = 5,
                 prunning: bool = False) -> list[list[str]]:
    """Find up to `no` valid paths from start to end using BFS.

    Uses a visited dictionary to prune redundant paths when pruning
    is enabled, returning early on the first valid path found.
    Falls back to an extended depth limit if no path is found within
    the default depth.

    Args:
        map_obj: The map containing zones, connections, and drone config.
        no: Maximum number of paths to return.
        prunning: If True, prune paths where a zone was already reached
                  at a lesser or equal depth, and return on first match.

    Returns:
        A list of paths, where each path is an ordered list of zone
        names from start to end. Returns an empty list if no path
        is found within the depth limit.
    """
    assert map_obj.end_zone is not None
    end: str = map_obj.end_zone

    paths: list[list[str]] = []
    queue: list[list[str]] = start_queue(map_obj)
    visited: dict[str, int] = {}
    extra: bool = False
    MAX_DEPTH: int = 50
    MAX_DEPTH_EXTREME: int = 60

    while queue:
        path: list[str] = queue.pop(0)
        depth: int = len(path)
        last = path[-1]

        if prunning:
            if last in visited and visited[last] <= depth:
                continue
            visited[last] = depth

            if last == end:
                return [path]

        if last == end:
            paths.append(path)

            if len(paths) == no:
                return paths
            continue
        elif depth >= MAX_DEPTH:
            if not paths:
                if not extra:
                    sys.stderr.write(f"[WARNING]: No paths found in a depth of {MAX_DEPTH}\n")
                    extra = True
                elif depth >= MAX_DEPTH_EXTREME:
                    sys.stderr.write(f"[ERROR]: No paths found in a depth of {MAX_DEPTH_EXTREME}\n")
                    return []
            else:
                return paths

        create_child_nodes(map_obj, queue, path)

    return paths


def create_child_nodes(map_obj: Map,
                       queue: list[list[str]],
                       path: list[str]) -> None:
    """Expand the current path by appending valid neighboring zones.

    Skips zones already in the current path (to avoid cycles) and
    zones of type BLOCKED.

    Args:
        map_obj: The map containing zones, connections, and drone config.
        queue: The BFS queue to append new paths to.
        path: The current path being expanded.
    """
    for zone in map_obj.adjacency[path[-1]]:
        if zone in path or \
           map_obj.zones[zone]["zone_type"] == ZoneType.BLOCKED:
            continue

        queue.append(path + [zone])


def start_queue(map_obj: Map) -> list[list[str]]:
    """Initialize the BFS queue with the start zone as the first path.

    Args:
        map_obj: The map containing zones, connections, and drone config.

    Returns:
        A list containing a single path with only the start zone.
    """
    assert map_obj.start_zone is not None
    return [[map_obj.start_zone]]
