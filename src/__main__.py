import sys
import os
from .parser import parser_map
from .map_model import Map
from .map_draw import display_map
from .bfs import create_paths
from .drone_asign import start_asign


def main() -> None:
    map_obj: Map
    drones_table: dict[int, dict[str, str]]

    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    try:
        map_obj = parser_map()
        paths: list[list[str]] = create_paths(map_obj, 10)
        drones_table = start_asign(map_obj, paths)
        display_map(map_obj, drones_table)

    except ValueError as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
