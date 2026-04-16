import pygame
from .map_model import Map
from .draw_helper import RenderData, soften, get_color, darken, get_last_known_location, get_position, get_offset, get_frame, get_float_offset, get_zone


def draw_turn(screen: pygame.Surface,
              font: pygame.font.Font,
              turn: int, status: str) -> None:

    text = font.render(f"{status} Turn {turn}", True, (220, 220, 220))
    rect = text.get_rect()
    rect.centerx = screen.get_width() // 2
    rect.top = 10

    bg = pygame.Surface((rect.width + 20, rect.height + 10), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 120))
    bg_rect = bg.get_rect(center=rect.center)

    shadow = font.render(f"{status} Turn {turn}", True, (0, 0, 0))
    shadow_rect = shadow.get_rect(center=(rect.centerx + 2, rect.centery + 2))

    screen.blit(bg, bg_rect)
    screen.blit(shadow, shadow_rect)
    screen.blit(text, rect)


def draw_connections(screen: pygame.Surface,
                     map_obj: Map, values: RenderData) -> None:

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


def draw_zones(screen: pygame.Surface,
               map_obj: Map,
               values: RenderData,
               time: int) -> None:

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
        if font_size < 40:
            continue

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


def draw_drones(screen: pygame.Surface,
                map_obj: Map,
                values: RenderData,
                drones_table: dict[int, dict[str, str]],
                current_turn: int,
                frames: tuple[list[pygame.Surface], list[pygame.Surface]],
                small_font: pygame.font.Font,
                transition_values: tuple[float, bool, bool]) -> None:
    if current_turn not in drones_table:
        return
    TRANSITION_DURATION = 500

    time = pygame.time.get_ticks()
    transition_start, animate_transition, is_transitioning = transition_values

    all_drones = {
        drone
        for turn_data in drones_table.values()
        for drone in turn_data
    }

    for drone in all_drones:
        loc_now = get_last_known_location(drones_table, drone, current_turn)
        loc_next = drones_table.get(current_turn + 1, {}).get(drone, loc_now)

        assert loc_now is not None
        assert loc_next is not None
        x1, y1 = get_position(map_obj, values, loc_now)
        x2, y2 = get_position(map_obj, values, loc_next)

        moving = animate_transition and is_transitioning \
            and loc_now != loc_next

        dx, dy = get_offset(drone)

        fx, fy = get_float_offset(time, drone)

        if is_transitioning:
            now = pygame.time.get_ticks()
            progress = (now - transition_start) / TRANSITION_DURATION
            progress = min(1, progress)
        else:
            progress = 0

        if moving:
            x = x1 + (x2 - x1) * progress + dx + fx
            y = y1 + (y2 - y1) * progress + dy + fy
            frame = get_frame(frames[1], time, drone)
        else:
            x = x1 + dx + fx
            y = y1 + dy + fy
            frame = get_frame(frames[0], time, drone)

        rect = frame.get_rect(center=(int(x), int(y)))
        screen.blit(frame, rect)

        radius = 12
        pygame.draw.circle(
            screen,
            (25, 25, 28, 0.8),
            (x + 15, y - 40),
            radius
        )

        label = drone[1:]
        text = small_font.render(label, True, (255, 255, 255))
        text_rect = text.get_rect(center=(int(x + 15), int(y - 40)))
        screen.blit(text, text_rect)


def draw_glow(values: RenderData,
              screen: pygame.Surface,
              rect: pygame.Rect,
              color: tuple[int, int, int],
              pulse: float) -> None:
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
