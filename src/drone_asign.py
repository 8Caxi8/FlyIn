import random
from .map_model import Map, ZoneType


class DataManagment():
    """Manages simulation state for drone path assignment.

    Tracks drone paths, zone capacities, and turn-by-turn drone
    positions during the sequential path assignment process.

    Attributes:
        max_drones: Total number of drones to route.
        map_obj: The map containing zones, connections, and drone config.
        paths: List of candidate paths from start to end.
        paths_len: Precomputed turn cost for each path.
        zone_capacity_table: Tracks zone/edge usage per turn.
        drones_table: Tracks drone positions per turn.
    """
    def __init__(self, map_obj: Map, paths: list[list[str]]) -> None:
        """Initialize DataManagment with a map and candidate paths.

        Args:
            map_obj: The map containing zones, connections, and drone config.
            paths: List of candidate paths from start to end.
        """
        self.max_drones = map_obj.drones
        self.map_obj: Map = map_obj
        self.paths = paths
        self.paths_len: list[int] = []
        self.capacity_table: dict[int, dict[str, int]] = {}
        self.drones_table: dict[int, dict[str, str]] = {}
        self.simulation: str = ""
        self.set_paths_len()

    def set_paths_len(self) -> None:
        """Precompute the turn cost for each candidate path.

        Counts 1 turn per normal/priority zone and 2 turns per
        restricted zone, excluding the start zone.
        """
        for path in self.paths:
            path_len = 0
            for zone in path:
                if zone == self.map_obj.start_zone:
                    continue

                if self.map_obj.zones[zone]["zone_type"] == \
                   ZoneType.RESTRICTED:
                    path_len += 1
                path_len += 1

            self.paths_len.append(path_len)


def start_asign(map_obj: Map,
                paths: list[list[str]]) -> dict[int, dict[str, str]]:
    """Route all drones sequentially and return the simulation table.

    Assigns each drone one at a time to the best available path,
    respecting capacity reservations made by previously assigned drones.

    Args:
        map_obj: The map containing zones, connections, and drone config.
        paths: List of candidate paths from start to end.

    Returns:
        A dict mapping each turn to a dict of drone IDs and their
        location at that turn (zone name or edge string).
    """
    data = DataManagment(map_obj, paths)
    drone = 1

    while drone <= data.max_drones:
        assign_next_drone(data, drone)
        drone += 1

    return data.drones_table


def assign_next_drone(data: DataManagment,
                      drone: int) -> None:
    """Select the best path for a drone and assign it.

    Simulates each candidate path against current reservations and
    picks the one with the lowest finish time. Ties are broken by
    the number of priority zones in the path.

    Args:
        data: The shared simulation state.
        drone: The drone ID to assign (1-indexed).
    """
    best_path = None
    best_time = float("inf")
    best_priority = -1

    for path in data.paths:
        finish_time, drone_movement = simulate_path(data, path)

        priority_count = sum(
            1
            for zone in path
            if data.map_obj.zones[zone]["zone_type"] == ZoneType.PRIORITY
        )

        if finish_time < best_time \
           or (finish_time == best_time and priority_count > best_priority):
            best_time = finish_time
            best_path = drone_movement
            best_priority = priority_count
        elif finish_time == best_time and priority_count == best_priority:
            if random.random() < 0.5:
                best_time = finish_time
                best_path = drone_movement
                best_priority = priority_count

    assert best_path is not None
    assert data.map_obj.start_zone is not None
    final_path = [data.map_obj.start_zone] + best_path
    asign_drone(data, final_path, drone)


def simulate_path(data: DataManagment,
                  path: list[str]) -> tuple[int, list[str]]:
    """Simulate a drone traversing a path against current reservations.

    Inserts wait steps wherever zone or edge capacity is exhausted.
    For restricted zones, checks both edge capacity at the current
    turn and zone capacity at the arrival turn before committing.

    Args:
        data: The shared simulation state.
        path: Ordered list of zone names from start to end.

    Returns:
        A tuple of (finish_turn, drone_path) where drone_path is the
        expanded sequence of zone names and 'wait' placeholders.
    """
    time: int = 1
    drone_path: list[str] = []

    for idx, zone in enumerate(path):
        if zone == data.map_obj.start_zone:
            continue
        prev_zone = path[idx - 1] if idx > 0 else data.map_obj.start_zone
        assert prev_zone is not None
        zones = (prev_zone, zone) if prev_zone < zone else (zone, prev_zone)
        edge = f"{zones[0]}-{zones[1]}"
        edge_cap = data.map_obj.connection_capacity[zones]
        edge_used = data.capacity_table.get(time, {}).get(edge, 0)

        if data.map_obj.zones[zone]["zone_type"] == ZoneType.RESTRICTED:
            while True:
                edge_used = data.capacity_table.get(time, {}).get(edge, 0)
                zone_used = data.capacity_table.get(
                    time + 1, {}).get(zone, 0)
                zone_cap = data.map_obj.zones[zone]["max_drones"]

                if edge_used < edge_cap and zone_used < zone_cap:
                    time += 1
                    drone_path.append(zone)
                    break
                drone_path.append("wait")
                time += 1
        else:
            while True:
                zone_used = data.capacity_table.get(time, {}).get(zone, 0)
                edge_used = data.capacity_table.get(time, {}).get(edge, 0)

                if zone_used < data.map_obj.zones[zone]["max_drones"] \
                   and edge_used < edge_cap:
                    break

                drone_path.append("wait")
                time += 1
            drone_path.append(zone)

        time += 1

    return time - 1, drone_path


def asign_drone(data: DataManagment,
                path: list[str],
                drone: int) -> None:
    """Commit a drone's expanded path into the simulation state.

    Updates both the zone capacity table and the drones table turn
    by turn. For restricted zones, also reserves the incoming edge
    for the transit turn.

    Args:
        data: The shared simulation state.
        path: Expanded path including 'wait' placeholders and start zone.
        drone: The drone ID being committed (1-indexed).
    """
    i = 1
    for idx, zone in enumerate(path):
        if zone == data.map_obj.start_zone:
            continue

        if zone == "wait":
            i += 1
            continue

        j = idx
        while path[j - 1] == "wait":
            j -= 1
        prev_zone = path[j - 1]
        edge = f"{prev_zone}-{zone}" if prev_zone < zone else f"{zone}-{prev_zone}"

        if data.map_obj.zones[zone]["zone_type"] == ZoneType.RESTRICTED:
            data.capacity_table.setdefault(i, {})
            no = data.capacity_table[i].get(edge, 0)
            data.capacity_table[i][edge] = no + 1

            data.drones_table.setdefault(i, {})
            data.drones_table[i][f"D{drone}"] = edge
            i += 1
        
        else:
            data.capacity_table.setdefault(i, {})
            no = data.capacity_table[i].get(edge, 0)
            data.capacity_table[i][edge] = no + 1

        data.capacity_table.setdefault(i, {})
        no = data.capacity_table[i].get(zone, 0)
        data.capacity_table[i][zone] = no + 1

        data.drones_table.setdefault(i, {})
        data.drones_table[i][f"D{drone}"] = zone
        i += 1


def print_simulation(drones_table: dict[int, dict[str, str]]) -> None:
    """Print the simulation output in the required format.

    Each turn is printed as a space-separated list of drone movements
    in the format D<ID>-<zone>, sorted by turn number.

    Args:
        drones_table: A dict mapping turns to drone position dicts.
    """
    for turn in drones_table:
        line: list[str] = []

        for drone, location in drones_table[turn].items():
            line.append(f"{drone}-{location}")
        print(" ".join(line))