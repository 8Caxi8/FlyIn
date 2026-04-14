from .map_model import Map, ZoneType


def check_solvability(map_obj: Map) -> bool:
    paths: list[list[str]] = create_paths(map_obj, 1, True)
    return bool(paths)


def create_paths(map_obj: Map,
                 no: int,
                 prunning: bool = False) -> list[list[str]]:
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
                    print("Thinking extra-hard!")
                    extra = True
                elif depth >= MAX_DEPTH_EXTREME:
                    print(f"Max Depth of {MAX_DEPTH_EXTREME} reached!")
                    return []
            else:
                return paths

        create_child_nodes(map_obj, queue, path)

    return paths


def create_child_nodes(map_obj: Map,
                       queue: list[list[str]],
                       path: list[str]) -> None:
    for zone in map_obj.adjacency[path[-1]]:
        if zone in path or \
           map_obj.zones[zone]["zone_type"] == ZoneType.BLOCKED:
            continue

        queue.append(path + [zone])


def start_queue(map_obj: Map) -> list[list[str]]:
    assert map_obj.start_zone is not None
    return [[map_obj.start_zone]]
