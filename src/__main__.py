import sys
import os
from .parser import parser_map
from .map_model import Map
from .map_draw import display_map
from .bfs import create_paths
from .drone_asign import start_asign


def main() -> None:
    """
    Execute the full drone pathfinding and simulation workflow.

    This function is the main entry point of the program and performs:

        1. Parse and validate the input map file
        2. Generate possible valid paths from start to goal
        3. Assign drones to the most efficient paths
        4. Build the simulation table of drone movements
        5. Launch the Pygame visualization window

    It also hides the default Pygame support prompt for cleaner output.

    If parsing, validation, or simulation fails, the error is printed
    and the program exits with status code 1.

    Returns:
        None
    """
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
