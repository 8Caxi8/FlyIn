import sys
import os
from .parser import parser_map
from .map_model import Map
from .map_draw import display_map
from .bfs import create_paths


def main() -> None:
    map_obj: Map

    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    try:
        map_obj = parser_map()
        paths: list[list[str]] = create_paths(map_obj, 10)
        for path in paths:
            print(" -> ".join(path))
        display_map(map_obj)

    except ValueError as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
