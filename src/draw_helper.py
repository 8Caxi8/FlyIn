from typing import NamedTuple
from .map_model import Map
import pygame
import math


class RenderData(NamedTuple):
    """
    Stores layout and rendering values used to draw the map.

    Attributes:
        node_size (int):
            Size in pixels of each zone square.

        spacing (float):
            Space in pixels between adjacent zones.

        offset (tuple[int, int]):
            Top-left screen offset used to center the map.

        min_x (int):
            Minimum x-coordinate found in the map.

        min_y (int):
            Minimum y-coordinate found in the map.
    """
    node_size: int
    spacing: float
    offset: tuple[int, int]
    min_x: int
    min_y: int


def compute_layout(map_obj: Map, WIDTH: int, HEIGHT: int) -> RenderData:
    """
    Compute the optimal layout values for rendering the map.

    Automatically scales node size and spacing so the full map fits
    inside the screen while preserving proportions and padding.

    Args:
        map_obj (Map):
            Parsed map object.

        WIDTH (int):
            Screen width in pixels.

        HEIGHT (int):
            Screen height in pixels.

    Returns:
        RenderData:
            Layout information used for rendering.
    """
    BASE_NODE = 150
    SPACING_RATIO = 0.3
    PADDING = 40

    min_x, max_x, min_y, max_y = get_bounds(map_obj)

    grid_w = max_x - min_x + 1
    grid_h = max_y - min_y + 1

    node_size = BASE_NODE
    spacing = int(node_size * SPACING_RATIO)

    used_w = grid_w * node_size + spacing * (grid_w - 1)
    used_h = grid_h * node_size + spacing * (grid_h - 1)

    available_w = WIDTH - 2 * PADDING
    available_h = HEIGHT - 2 * PADDING

    if used_w > available_w or used_h > available_h:
        scale = min(
            available_w / used_w,
            available_h / used_h
        )

        node_size = int(BASE_NODE * scale)
        spacing = int(node_size * SPACING_RATIO)

        used_w = grid_w * node_size + spacing * (grid_w - 1)
        used_h = grid_h * node_size + spacing * (grid_h - 1)

    offset = (
        PADDING + (available_w - used_w) // 2,
        PADDING + (available_h - used_h) // 2
    )

    return RenderData(
        node_size,
        spacing,
        offset,
        min_x,
        min_y,
    )


def get_last_known_location(drones_table: dict[int, dict[str, str]],
                            drone: str,
                            current_turn: int) -> str:
    """
    Retrieve the last known position of a drone up to a given turn.

    Used when a drone is waiting and does not explicitly appear
    in the current turn entry.

    Args:
        drones_table (dict[int, dict[str, str]]):
            Simulation table of drone positions.

        drone (str):
            Drone identifier (example: "D3").

        current_turn (int):
            Current simulation turn.

    Returns:
        str:
            Last known location of the drone.

    Raises:
        ValueError:
            If no previous location is found.
    """
    for t in range(current_turn, -1, -1):
        if drone in drones_table.get(t, {}):
            return drones_table[t][drone]

    raise ValueError(f"Last position unreacheble in {drones_table}")


def get_position(map_obj: Map,
                 values: RenderData,
                 location: str) -> tuple[int, int]:
    """
    Convert a drone location string into screen coordinates.

    If the location is an edge ("A-B"), returns the midpoint
    between both connected zones.

    If the location is a zone name, returns the center position
    of that zone.

    Args:
        map_obj (Map):
            Parsed map object.

        values (RenderData):
            Rendering layout values.

        location (str):
            Zone name or edge representation.

    Returns:
        tuple[int, int]:
            Screen position in pixels.
    """
    if "-" in location:
        a, b = location.split("-", 1)

        ax, ay = get_node_pos(map_obj, values, a)
        bx, by = get_node_pos(map_obj, values, b)

        return ((ax + bx) // 2, (ay + by) // 2)

    return get_node_pos(map_obj, values, location)


def get_node_pos(map_obj: Map,
                 values: RenderData,
                 zone: str) -> tuple[int, int]:
    """
    Convert a zone name into the center screen position of that node.

    Args:
        map_obj (Map):
            Parsed map object.

        values (RenderData):
            Rendering layout values.

        zone (str):
            Zone name.

    Returns:
        tuple[int, int]:
            Center pixel coordinates of the zone.
    """
    x, y = map_obj.zones[zone]["position"]

    px = (
        (x - values.min_x) * (values.node_size + values.spacing)
        + values.offset[0]
    )

    py = (
        (y - values.min_y) * (values.node_size + values.spacing)
        + values.offset[1]
    )

    return px + values.node_size // 2, py + values.node_size // 2


def get_frame(frames: list[pygame.Surface],
              time: int,
              drone: str) -> pygame.Surface:
    """
    Select the current animation frame for a drone.

    Uses a hash-based phase offset so drones do not animate
    perfectly in sync.

    Args:
        frames (list[pygame.Surface]):
            Animation frame list.

        time (int):
            Current pygame tick time.

        drone (str):
            Drone identifier.

    Returns:
        pygame.Surface:
            Current animation frame.
    """
    ANIM_SPEED = 150

    offset = hash(drone) % 1000

    index = ((time + offset) // ANIM_SPEED) % len(frames)

    return frames[index]


def get_bounds(map_obj: Map) -> tuple[int, int, int, int]:
    """
    Get the minimum and maximum map coordinates.

    Args:
        map_obj (Map):
            Parsed map object.

    Returns:
        tuple[int, int, int, int]:
            (min_x, max_x, min_y, max_y)
    """
    x_vals = [data["position"][0] for data in map_obj.zones.values()]
    y_vals = [data["position"][1] for data in map_obj.zones.values()]

    return min(x_vals), max(x_vals), min(y_vals), max(y_vals)


def get_color(color: str | None) -> tuple[int, int, int]:
    """
    Convert a color name into an RGB tuple.

    Falls back to cyan if the color is invalid or missing.

    Args:
        color (str | None):
            Color name.

    Returns:
        tuple[int, int, int]:
            RGB color tuple.
    """
    if color:
        try:
            c = pygame.Color(color)
            return c.r, c.g, c.b
        except ValueError:
            pass

    return 0, 200, 255


def soften(color: tuple[int, int, int]) -> tuple[int, int, int]:
    """
    Slightly soften a color for visual styling.

    Args:
        color (tuple[int, int, int]):
            RGB color.

    Returns:
        tuple[int, int, int]:
            Softened RGB color.
    """
    r, g, b = color
    return (
        int(r * 0.85),
        int(g * 0.85),
        int(b * 0.85)
    )


def darken(color: tuple[int, int, int],
           factor: float = 0.7) -> tuple[int, int, int]:
    """
    Darken a color by a multiplication factor.

    Args:
        color (tuple[int, int, int]):
            RGB color.

        factor (float):
            Darkening multiplier.

    Returns:
        tuple[int, int, int]:
            Darkened RGB color.
    """
    r, g, b = color
    return (
        int(r * factor),
        int(g * factor),
        int(b * factor)
    )


def load_animations(idle_path: str, mov_path: str, frame_count: int) \
                        -> tuple[list[pygame.Surface], list[pygame.Surface]]:
    """
    Load and split idle and movement animation spritesheets.

    Each spritesheet is assumed to contain frames arranged
    horizontally in a single row.

    The function divides each spritesheet into individual frames
    and returns both animation frame lists.

    Args:
        idle_path (str):
            Path to the idle animation spritesheet.

        mov_path (str):
            Path to the movement animation spritesheet.

        frame_count (int):
            Number of frames contained in each spritesheet.

    Returns:
        tuple[list[pygame.Surface], list[pygame.Surface]]:
            A tuple containing:
                - idle animation frames
                - movement animation frames

    Raises:
        ValueError:
            If the image files cannot be loaded.
    """
    try:
        idle = pygame.image.load(idle_path).convert_alpha()
        mov = pygame.image.load(mov_path).convert_alpha()
    except (pygame.error, FileNotFoundError) as e:
        raise ValueError(e)

    idle_frame_w = idle.get_width() // frame_count
    idle_frame_h = idle.get_height()

    mov_frame_w = mov.get_width() // frame_count
    mov_frame_h = mov.get_height()

    idle_frames = []
    for i in range(frame_count):
        frame = idle.subsurface((i * idle_frame_w, 0, idle_frame_w,
                                idle_frame_h))
        idle_frames.append(frame)

    mov_frames = []
    for i in range(frame_count):
        frame = mov.subsurface((i * mov_frame_w, 0, mov_frame_w,
                                mov_frame_h))
        mov_frames.append(frame)

    return idle_frames, mov_frames


def add_turn_zero(map_obj: Map,
                  drones_table: dict[int, dict[str, str]]) \
                    -> dict[int, dict[str, str]]:
    """
    Add turn 0 to the simulation table.

    At turn 0, all drones start at the start zone before any
    movement begins.

    This ensures every drone always has an initial known position.

    Args:
        map_obj (Map):
            Parsed map containing the start zone and total number
            of drones.

        drones_table (dict[int, dict[str, str]]):
            Existing simulation table.

    Returns:
        dict[int, dict[str, str]]:
            Updated simulation table including turn 0.
    """
    assert map_obj.start_zone is not None

    drones_table[0] = {
        f"D{i}": map_obj.start_zone
        for i in range(1, map_obj.drones + 1)
    }

    return drones_table


def get_offset(drone: str,
               spread: float = 10) -> tuple[float, float]:
    """
    Generate a stable visual offset for a drone.

    This prevents multiple drones occupying the same zone from
    being drawn directly on top of each other.

    The offset is deterministic based on the drone identifier.

    Args:
        drone (str):
            Drone identifier.

        spread (float):
            Maximum offset spread in pixels.

    Returns:
        tuple[float, float]:
            (dx, dy) positional offset.
    """
    h = hash(drone)

    dx = ((h & 0xFF) / 255 - 0.5) * 2 * spread
    dy = (((h >> 8) & 0xFF) / 255 - 0.5) * 2 * spread

    return dx, dy


def get_float_offset(time: int,
                     drone: str) -> tuple[float, float]:
    """
    Generate a small floating animation offset for a drone.

    This creates a subtle hovering effect so drones feel less static
    while idle.

    Each drone gets a slightly different phase so animations do not
    sync perfectly.

    Args:
        time (int):
            Current pygame tick time.

        drone (str):
            Drone identifier.

    Returns:
        tuple[float, float]:
            (dx, dy) floating animation offset.
    """
    speed = 0.00001
    amplitude = 3

    phase = hash(drone) % 1000

    dy = amplitude * math.sin(time * speed * phase)
    dx = 0.5 * amplitude * math.cos(time * speed * phase)

    return dx, dy


def get_zone(location: str) -> str:
    """
    Extract the destination zone from a location string.

    If the location represents an edge ("A-B"), returns the
    destination zone ("B").

    If the location is already a zone name, returns it unchanged.

    Used to compare logical drone positions instead of raw
    string representations.

    Args:
        location (str):
            Zone name or edge representation.

    Returns:
        str:
            Destination zone name.
    """
    if "-" in location:
        return location.split("-")[1]

    return location
