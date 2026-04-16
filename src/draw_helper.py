from typing import NamedTuple
from .map_model import Map
import pygame
import math


class RenderData(NamedTuple):
    node_size: int
    spacing: float
    offset: tuple[int, int]
    min_x: int
    min_y: int


def compute_layout(map_obj: Map, WIDTH: int, HEIGHT: int) -> RenderData:
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
    for t in range(current_turn, -1, -1):
        if drone in drones_table.get(t, {}):
            return drones_table[t][drone]

    raise ValueError(f"Last position unreacheble in {drones_table}")


def get_position(map_obj: Map,
                 values: RenderData,
                 location: str) -> tuple[int, int]:
    if "-" in location:
        a, b = location.split("-", 1)

        ax, ay = get_node_pos(map_obj, values, a)
        bx, by = get_node_pos(map_obj, values, b)

        return ((ax + bx) // 2, (ay + by) // 2)

    return get_node_pos(map_obj, values, location)


def get_node_pos(map_obj: Map,
                 values: RenderData,
                 zone: str) -> tuple[int, int]:
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
    ANIM_SPEED = 150

    offset = hash(drone) % 1000

    index = ((time + offset) // ANIM_SPEED) % len(frames)

    return frames[index]


def get_bounds(map_obj: Map) -> tuple[int, int, int, int]:
    x_vals = [data["position"][0] for data in map_obj.zones.values()]
    y_vals = [data["position"][1] for data in map_obj.zones.values()]

    return min(x_vals), max(x_vals), min(y_vals), max(y_vals)


def compute_scale(map_obj: Map, screen_width: int,
                  padding: int, screen_height: int) -> tuple[float, float]:
    min_x, max_x, min_y, max_y = get_bounds(map_obj)

    map_width = max_x - min_x + 1
    map_height = max_y - min_y + 1

    scale_x = (screen_width - 2 * padding) / map_width
    scale_y = (screen_height - 2 * padding) / map_height

    return scale_x, scale_y


def get_color(color: str | None) -> tuple[int, int, int]:
    if color:
        try:
            c = pygame.Color(color)
            return c.r, c.g, c.b
        except ValueError:
            pass

    return 0, 200, 255


def soften(color: tuple[int, int, int]) -> tuple[int, int, int]:
    r, g, b = color
    return (
        int(r * 0.85),
        int(g * 0.85),
        int(b * 0.85)
    )


def darken(color: tuple[int, int, int],
           factor: float = 0.7) -> tuple[int, int, int]:
    r, g, b = color
    return (
        int(r * factor),
        int(g * factor),
        int(b * factor)
    )


def load_animations(idle_path: str, mov_path: str, frame_count: int) \
                        -> tuple[list[pygame.Surface], list[pygame.Surface]]:
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
    assert map_obj.start_zone is not None

    drones_table[0] = {
        f"D{i}": map_obj.start_zone
        for i in range(1, map_obj.drones + 1)
    }

    return drones_table


def get_offset(drone: str,
               spread: float = 10) -> tuple[float, float]:
    h = hash(drone)

    dx = ((h & 0xFF) / 255 - 0.5) * 2 * spread
    dy = (((h > 8) & 0xFF) / 255 - 0.5) * 2 * spread

    return dx, dy


def get_float_offset(time: int,
                     drone: str) -> tuple[float, float]:
    speed = 0.00001
    amplitude = 3

    phase = hash(drone) % 1000

    dy = amplitude * math.sin(time * speed * phase)
    dx = 0.5 * amplitude * math.cos(time * speed * phase)

    return dx, dy


def get_zone(location: str) -> str:
    if "-" in location:
        return location.split("-")[1]

    return location
