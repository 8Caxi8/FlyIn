import sys
import os
from .parser import parser_map
from .map_model import Map
from .map_draw import display_map


def main() -> None:
    map_obj: Map

    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    try:
        map_obj = parser_map()
        display_map(map_obj)

    except ValueError as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
