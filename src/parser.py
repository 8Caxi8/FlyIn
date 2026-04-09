import sys
from .map_model import Map, MapError, Zone, Connection


class FileError(Exception):
    pass


class HubError(FileError):
    def __str__(self) -> str:
        return ("Each hub line must have the format:\n"
                "    start_hub/end_hub/hub: "
                "<name> <x> <y> [metadata]\n\n"
                "All metadata should be enclosed in []:\n"
                "    zone=<type>\n"
                "    color=<value>\n"
                "    max_drones=<number>\n")


class ConnectionError(FileError):
    def __str__(self) -> str:
        return ("Each connection line must have the format:\n"
                "    connection: "
                "<name1>-<name2> [metadata]\n\n"
                "All metadata should be enclosed in []:\n"
                "    max_link_capacity=<number>\n")


def parser_map() -> Map:
    args = sys.argv[1:]
    i = 0

    map_path = "default.txt"

    while i < len(args):
        if args[i] == "--input":
            if i + 1 >= len(args):
                raise ValueError("Missing value for '--input'")
            map_path = args[i + 1]
            break

        i += 1

    return load_map(map_path)


def load_map(map_path: str) -> Map:
    map_obj: Map | None = None

    try:
        with open(map_path, "r") as f:
            for line in f:
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                parts = line.split()
                if map_obj is None:
                    if parts[0] != "nb_drones:":
                        raise FileError("Map must start by stating number of "
                                        "drones with: 'nb_drones:'")

                    map_obj = Map(parts[1])
                else:
                    if "[" in line:
                        if not parts[-1].endswith("]"):
                            raise HubError()

                        main_part, meta_part = line.split("[", 1)
                    else:
                        main_part = line
                        meta_part = ""

                    maindata = main_part.split()

                    if maindata[0].startswith(("hub:",
                                               "start_hub:",
                                               "end_hub:")):
                        metadata = parse_metadata("zone", meta_part.strip("]"))

                        if len(maindata) != 4:
                            raise HubError()

                        name, x, y = maindata[1:]

                        zone = Zone(name=name, x=int(x), y=int(y),
                                    **metadata)

                        match maindata[0]:
                            case "start_hub:":
                                map_obj.set_start_zone(zone)

                            case "end_hub:":
                                map_obj.set_end_zone(zone)

                            case "hub:":
                                map_obj.add_zone(zone)

                    elif maindata[0] == "connection:":
                        if len(maindata) != 2:
                            raise ConnectionError()

                        metadata = parse_metadata("conn", meta_part.strip("]"))

                        conn_names = maindata[1].split("-", 1)

                        if len(conn_names) != 2:
                            raise ConnectionError()

                        name1, name2 = conn_names

                        connection = Connection(zone1=name1, zone2=name2,
                                                **metadata)
                        map_obj.add_connection(connection)

                    else:
                        raise FileError("Every line must define a hub or a "
                                        "connection with:\n"
                                        "    start_hub/hub/end_hub:\n"
                                        "    connection:")

        if map_obj is None:
            raise FileError("Missing nb_drones:")
        map_obj.check_map()

    except (OSError, FileError, MapError) as e:
        raise ValueError(f"[ParsingError]: {e}")

    return map_obj


def parse_metadata(meta_type: str, meta: str) -> dict[str, str | int]:
    result: dict[str, str | int] = {}
    meta_keys = {"zone", "color", "max_drones"} \
        if meta_type == "zone" else {"max_link_capacity"}

    if not meta:
        return result

    for item in meta.split():
        if "=" not in item:
            if meta_type == "zone":
                raise HubError()
            else:
                raise ConnectionError()

        key, value = item.split("=", 1)

        if key not in meta_keys:
            if meta_type == "zone":
                raise HubError()
            else:
                raise ConnectionError()

        result[key] = value

    return result
