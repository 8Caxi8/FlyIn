from .map_model import Map
from typing import NamedTuple, Any


class RenderData(NamedTuple):
    node_size: int
    spacing: float
    offset: tuple[int, int]
    min_x: int
    min_y: int


def display_map(map_obj: Map) -> None:
    import pygame

    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Drone Map")
    width, height = screen.get_size()

    values = compute_layout(map_obj, width, height)

    clock = pygame.time.Clock()

    running = True

    while running:
        screen.fill((25, 25, 28))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        time = pygame.time.get_ticks()
        draw_connections(screen, map_obj, values)
        draw_zones(screen, map_obj, values, time)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


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


def draw_connections(screen: Any, map_obj: Map, values: RenderData) -> None:
    import pygame

    for connection in list(map_obj.connections):
        a, b = connection
        data_a = map_obj.zones.get(a)
        data_b = map_obj.zones.get(b)

        if not data_a or not data_b:
            continue

        a_x, a_y = data_a["position"]
        b_x, b_y = data_b["position"]

        start = (
            (a_x - values.min_x) * (values.node_size + values.spacing)
            + values.offset[0]
            + values.node_size // 2,
            (a_y - values.min_y) * (values.node_size + values.spacing)
            + values.offset[1]
            + values.node_size // 2,
        )

        end = (
            (b_x - values.min_x) * (values.node_size + values.spacing)
            + values.offset[0]
            + values.node_size // 2,
            (b_y - values.min_y) * (values.node_size + values.spacing)
            + values.offset[1]
            + values.node_size // 2,
        )

        pygame.draw.line(screen, (20, 20, 20), start, end, 5)
        pygame.draw.line(screen, (180, 180, 180), start, end, 3)

        pygame.draw.circle(screen, (180, 180, 180), start, 2)
        pygame.draw.circle(screen, (180, 180, 180), end, 2)


def draw_zones(screen: Any,
               map_obj: Map,
               values: RenderData,
               time: int) -> None:
    import pygame

    for name, data in map_obj.zones.items():
        x, y = data["position"]
        color = soften(get_color(data["color"]))

        node_x = (
            (x - values.min_x) * (values.node_size + values.spacing)
            + values.offset[0]
        )

        node_y = (
            (y - values.min_y) * (values.node_size + values.spacing)
            + values.offset[1]
        )

        rect = pygame.Rect(
            node_x,
            node_y,
            values.node_size,
            values.node_size,
        )

        if name in {map_obj.start_zone, map_obj.end_zone}:
            pulse = (time % 2400) / 2400
            draw_glow(values, screen, rect, color, pulse)

            pulse2 = ((time + 1200) % 2400) / 2400
            draw_glow(values, screen, rect, color, pulse2)

        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, darken(color, 0.55), rect, 2, border_radius=8)
        pygame.draw.rect(screen, (220, 220, 220), rect, 1, border_radius=8)

        highlight = rect.inflate(-6, -6)
        highlight.height //= 2
        pygame.draw.rect(
            screen,
            tuple(min(255, c + 35) for c in color),
            highlight,
            border_radius=6
        )

        font_size = int(values.node_size * 0.5)
        font = pygame.font.Font(None, font_size)

        text = font.render(name, True, (255, 255, 255))

        while (
            text.get_width() > values.node_size + 6
            or text.get_height() > values.node_size + 6
        ) and font_size > 10:
            font_size -= 1
            font = pygame.font.Font(None, font_size)
            text = font.render(name, True, (255, 255, 255))

        text = pygame.transform.rotate(text, 30)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)


def draw_glow(values: RenderData,
              screen: Any,
              rect: Any,
              color: tuple[int, int, int],
              pulse: float) -> None:
    import pygame
    MAX_RADIUS = 50

    radius = int(values.node_size / 2 + pulse * MAX_RADIUS)
    alpha = int(120 * (1 - pulse))

    glow_surface = pygame.Surface(
        (radius * 2, radius * 2),
        pygame.SRCALPHA
    )

    pygame.draw.circle(
        glow_surface,
        (*color, alpha),
        (radius, radius),
        radius,
    )

    screen.blit(
        glow_surface,
        (rect.centerx - radius, rect.centery - radius)
    )


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
    import pygame
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
