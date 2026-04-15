from .map_model import Map, ZoneType


class DataManagment():
    def __init__(self, map_obj: Map, paths: list[list[str]]) -> None:
        self.max_drones = map_obj.drones
        self.map_obj: Map = map_obj
        self.paths = paths
        self.paths_len: list[int] = []
        self.zone_capacity_table: dict[int, dict[str, int]] = {}
        self.drones_table: dict[int, dict[str, str]] = {}
        self.set_paths_len()

    def set_paths_len(self) -> None:
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
    data = DataManagment(map_obj, paths)

    asign_first_drone(data)

    drone = 2
    while drone <= data.max_drones:
        asign_next_drone(data, drone)
        drone += 1

    print_simulation(data.drones_table)
    return data.drones_table


def asign_first_drone(data: DataManagment) -> None:
    path = data.paths[0]

    i = 1
    for idx, zone in enumerate(path):
        if zone == data.map_obj.start_zone:
            continue

        if data.map_obj.zones[zone]["zone_type"] == ZoneType.RESTRICTED:
            prev = path[idx - 1]
            data.zone_capacity_table[i] = {f"{prev}-{zone}": 1}
            data.drones_table[i] = {"D1": f"{prev}-{zone}"}
            i += 1
        data.zone_capacity_table[i] = {zone: 1}
        data.drones_table[i] = {"D1": zone}
        i += 1


def asign_next_drone(data: DataManagment,
                     drone: int) -> None:
    best_path = None
    best_time = float("inf")

    for path in data.paths:
        drone_movement = simulate_path(data, path)
        finish_time = len(drone_movement)

        if finish_time < best_time:
            best_time = finish_time
            best_path = drone_movement

    assert best_path is not None
    assert data.map_obj.start_zone is not None
    best_path.insert(0, data.map_obj.start_zone)
    asign_drone(data, best_path, drone)


def simulate_path(data: DataManagment,
                  path: list[str]) -> list[str]:
    time: int = 1
    drone_path: list[str] = []

    for idx, zone in enumerate(path):
        if zone == data.map_obj.start_zone:
            continue

        if data.map_obj.zones[zone]["zone_type"] == ZoneType.RESTRICTED:
            while True:
                prev = path[idx - 1]
                zones = (prev, zone) if prev < zone else (zone, prev)
                edge = f"{prev}-{zone}"

                edge_used = data.zone_capacity_table.get(time, {}).get(edge, 0)
                edge_cap = data.map_obj.connection_capacity[zones]

                zone_used = data.zone_capacity_table.get(
                    time + 1, {}).get(zone, 0)
                zone_cap = data.map_obj.zones[zone]["max_drones"]

                if edge_used < edge_cap and zone_used < zone_cap:
                    time += 1
                    drone_path.append(zone)
                    break
                time += 1
                drone_path.append("wait")
        else:
            while data.zone_capacity_table.get(time, {}).get(zone, 0) >= \
             data.map_obj.zones[zone]["max_drones"]:
                time += 1
                drone_path.append("wait")
            drone_path.append(zone)

        time += 1

    return drone_path


def asign_drone(data: DataManagment,
                path: list[str],
                drone: int) -> None:
    i = 1
    for idx, zone in enumerate(path):
        if zone == data.map_obj.start_zone:
            continue

        if zone == "wait":
            i += 1
            continue

        if data.map_obj.zones[zone]["zone_type"] == ZoneType.RESTRICTED:
            back = idx - 1
            while path[back] == "wait":
                back -= 1
            prev = path[back]

            data.zone_capacity_table.setdefault(i, {})
            no = data.zone_capacity_table[i].get(f"{prev}-{zone}", 0)
            data.zone_capacity_table[i][f"{prev}-{zone}"] = no + 1

            data.drones_table.setdefault(i, {})
            data.drones_table[i][f"D{drone}"] = f"{prev}-{zone}"
            i += 1

        data.zone_capacity_table.setdefault(i, {})
        no = data.zone_capacity_table[i].get(zone, 0)
        data.zone_capacity_table[i][zone] = no + 1

        data.drones_table.setdefault(i, {})
        data.drones_table[i][f"D{drone}"] = zone
        i += 1


def print_simulation(drones_table: dict[int, dict[str, str]]) -> None:
    for turn in drones_table:
        line: list[str] = []

        for drone, location in drones_table[turn].items():
            line.append(f"{drone}-{location}")
        print(" ".join(line))
