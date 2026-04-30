import sys
from .map_model import Map, MapError, Zone, Connection
from .bfs import check_solvability


class FileError(Exception):
    """Base exception for all map file parsing errors."""
    pass


class HubError(FileError):
    """Raised when a hub definition line has an invalid format."""
    def __str__(self) -> str:
        return ("Each hub line must have the format:\n"
                "    start_hub/end_hub/hub: "
                "<name> <x> <y> [metadata]\n\n"
                "All metadata should be enclosed in []:\n"
                "    zone=<type>\n"
                "    color=<value>\n"
                "    max_drones=<number>\n")


class ConnectionError(FileError):
    """Raised when a connection definition line has an invalid format."""
    def __str__(self) -> str:
        return ("Each connection line must have the format:\n"
                "    connection: "
                "<name1>-<name2> [metadata]\n\n"
                "All metadata should be enclosed in []:\n"
                "    max_link_capacity=<number>\n")


def parser_map() -> tuple[bool,Map]:
    """
    Parse command-line arguments and load the corresponding map file.

    Looks for the optional '--input' flag to determine the input file path.
    If not provided, falls back to 'default.txt' and emits a warning to stderr.
    Looks for the optional '--no-gui' flag to disable the graphical interface.

    Returns:
        tuple[bool, Map]: A tuple of (gui_enabled, parsed_map) where
            gui_enabled is True unless '--no-gui' was passed, and
            parsed_map is the fully parsed and validated Map object.

    Raises:
        ValueError: If '--input' is provided without a following file path,
                    or if the map file fails parsing or validation.
    """
    args = sys.argv[1:]
    map_path = "default.txt"
    gui = True

    if "--input" in args:
        idx = args.index("--input")
        try:
            map_path = args[idx + 1]
        except IndexError:
            raise ValueError("Missing value for '--input'")
    
    else:
        sys.stderr.write("[WARNING]: No --input received, falling back to 'default.txt'.\n")
                         
    if "--no-gui" in args:
        gui = False
    

    return gui, load_map(map_path)


def load_map(map_path: str) -> Map:
    """
    Load, parse, validate, and verify solvability of a map file.

    Reads the map definition file, creates all zones and connections,
    validates the map structure, and ensures at least one valid path
    exists between the start and end zones.

    Args:
        map_path (str): Path to the map definition file.

    Returns:
        Map: A fully parsed and validated map object.

    Raises:
        ValueError:
            If the file cannot be read, contains invalid formatting,
            violates map validation rules, or is not solvable.
    """
    map_obj: Map | None = None

    try:
        with open(map_path, "r") as f:
            for line in f:
                line = line.strip().split("#", 1)[0]

                if not line:
                    continue

                parts = line.split()
                if map_obj is None:
                    if parts[0] != "nb_drones:" or len(parts) != 2 :
                        raise FileError("Map must start by stating number of "
                                        "drones with: 'nb_drones: <no_drones>'")

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
                        metadata = parse_metadata(
                            "zone", meta_part.rstrip("]"))

                        if len(maindata) != 4:
                            raise HubError()

                        name, x, y = maindata[1:]

                        try:
                            zone = Zone(name=name, x=int(x), y=int(y),
                                    **metadata)
                        except ValueError as e:
                            raise HubError(e)

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

    if not check_solvability(map_obj):
        raise ValueError("[ParsingError]: Map is not solvable!")

    return map_obj


def parse_metadata(meta_type: str, meta: str) -> dict[str, str | int]:
    """
    Parse metadata values from a hub or connection definition line.

    Converts metadata strings such as:
        zone=restricted color=blue max_drones=3

    into a dictionary suitable for Zone or Connection construction.

    For zones, the key 'zone' is renamed to 'zone_type'.

    Args:
        meta_type (str):
            Type of metadata being parsed.
            Expected values:
                - 'zone' for hub metadata
                - 'conn' for connection metadata

        meta (str):
            Raw metadata string without surrounding brackets.

    Returns:
        dict[str, str | int]:
            Parsed metadata dictionary.

    Raises:
        HubError:
            If hub metadata is malformed or contains invalid keys.

        ConnectionError:
            If connection metadata is malformed or contains invalid keys.
    """
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

        if key == "zone":
            key = "zone_type"

        result[key] = value

    return result
