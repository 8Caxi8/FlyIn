import pygame
from .map_model import Map
from .draw_helper import (RenderData, soften, get_color, darken,
                          get_last_known_location, get_position,
                          get_offset, get_frame, get_float_offset)


def draw_turn(
    screen: pygame.Surface,
    font: tuple[pygame.font.Font, pygame.font.Font],
    turn: int,
    max_turn: int,
    status: str
) -> None:
    """
    Draw the current simulation turn indicator at the top-center
    of the screen.

    Displays:
        - Play/Pause status symbol
        - Current turn number
        - Maximum turn count

    A semi-transparent background and shadow text are used to improve
    readability.

    Args:
        screen (pygame.Surface):
            Main rendering surface.

        font (tuple[pygame.font.Font, pygame.font.Font]):
            Tuple containing:
                - normal font
                - bold font

        turn (int):
            Current simulation turn.

        max_turn (int):
            Final simulation turn.

        status (str):
            Playback state symbol ("▶" for play, "||" for pause).

    Returns:
        None
    """
    normal_font, bold_font = font

    if status == "▶":
        status_text = bold_font.render(status, True, (220, 220, 220))
    else:
        status_text = normal_font.render(status, True, (220, 220, 220))

    turn_text = bold_font.render(
        f"Turn {turn} / {max_turn}",
        True,
        (220, 220, 220)
    )

    total_width = status_text.get_width() + 10 + turn_text.get_width()
    total_height = max(
        status_text.get_height(),
        turn_text.get_height()
    )

    center_x = screen.get_width() // 2
    top_y = 40

    start_x = center_x - total_width // 2

    status_rect = status_text.get_rect()
    if status == "▶":
        status_rect.x = start_x
        status_rect.top = top_y
    else:
        status_rect.x = start_x + 5
        status_rect.top = top_y + 10

    turn_rect = turn_text.get_rect()
    turn_rect.x = status_rect.right + 10
    turn_rect.top = top_y

    bg = pygame.Surface(
        (total_width + 30, total_height + 20),
        pygame.SRCALPHA
    )
    bg.fill((0, 0, 0, 120))

    bg_rect = bg.get_rect(
        center=(center_x, top_y + total_height // 2)
    )

    shadow_status = (
        bold_font if status == "▶" else normal_font
    ).render(status, True, (0, 0, 0))

    shadow_turn = bold_font.render(
        f"Turn {turn} / {max_turn}",
        True,
        (0, 0, 0)
    )

    shadow_status_rect = status_rect.move(2, 2)
    shadow_turn_rect = turn_rect.move(2, 2)

    screen.blit(bg, bg_rect)
    screen.blit(shadow_status, shadow_status_rect)
    screen.blit(shadow_turn, shadow_turn_rect)
    screen.blit(status_text, status_rect)
    screen.blit(turn_text, turn_rect)


def draw_commands(screen: pygame.Surface) -> None:
    """
    Draw the control help panel in the bottom-left corner.

    Displays available keyboard commands used to control
    the simulation playback and navigation.

    Args:
        screen (pygame.Surface):
            Main rendering surface.

    Returns:
        None
    """
    font = pygame.font.Font(None, 25)
    title_font = pygame.font.Font(None, 30)

    title = "Commands"
    commands = [
        "SPACE > Play / Pause",
        "A > Previous Turn",
        "D > Next Turn",
        "S > Reset to Turn 0",
        "Q > Quit",
    ]

    padding = 20
    line_spacing = 8

    x = padding
    y = screen.get_height() - 180

    title_text = title_font.render(title, True, (240, 240, 240))
    screen.blit(title_text, (x, y))

    y += title_text.get_height() + 12

    for command in commands:
        text = font.render(command, True, (220, 220, 220))
        screen.blit(text, (x, y))
        y += text.get_height() + line_spacing


def draw_connections(screen: pygame.Surface,
                     map_obj: Map, values: RenderData) -> None:
    """
    Draw all connections (edges) between zones.

    Each connection is rendered as a line between the center
    points of two connected zones, with a darker outline
    for better visual depth.

    Args:
        screen (pygame.Surface):
            Main rendering surface.

        map_obj (Map):
            Parsed map containing zones and connections.

        values (RenderData):
            Layout values used for rendering.

    Returns:
        None
    """

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
    """
    Draw all map zones (nodes).

    Zones are rendered as rounded squares with:
        - base color
        - border styling
        - highlight effect
        - optional glowing animation for start/end zones
        - rotated zone label if space allows

    Args:
        screen (pygame.Surface):
            Main rendering surface.

        map_obj (Map):
            Parsed map containing all zones.

        values (RenderData):
            Layout values used for rendering.

        time (int):
            Current pygame tick time used for glow animation.

    Returns:
        None
    """

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
    """
    Draw all drones for the current simulation turn.

    Supports:
        - idle animation while stationary
        - movement animation during turn transitions
        - smooth interpolation between turns
        - floating idle motion
        - per-drone positional offset to avoid overlap
        - numeric drone labels

    Drones positioned on edges are rendered at the midpoint
    between connected zones.

    Args:
        screen (pygame.Surface):
            Main rendering surface.

        map_obj (Map):
            Parsed map object.

        values (RenderData):
            Layout values used for rendering.

        drones_table (dict[int, dict[str, str]]):
            Simulation table containing drone positions per turn.

        current_turn (int):
            Current simulation turn.

        frames (tuple[list[pygame.Surface], list[pygame.Surface]]):
            Tuple containing:
                - idle animation frames
                - movement animation frames

        small_font (pygame.font.Font):
            Font used for drone labels.

        transition_values (tuple[float, bool, bool]):
            Tuple containing:
                - transition start time
                - whether transition animation is enabled
                - whether transition is currently active

    Returns:
        None
    """
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
        loc_prev = get_last_known_location(drones_table,
                                           drone, current_turn - 1) \
            if current_turn > 0 else loc_now

        assert loc_now is not None
        assert loc_prev is not None
        x1, y1 = get_position(map_obj, values, loc_prev)
        x2, y2 = get_position(map_obj, values, loc_now)

        actually_moved = loc_prev != loc_now
        moving = animate_transition and is_transitioning and actually_moved

        dx, dy = get_offset(drone)
        fx, fy = get_float_offset(time, drone)

        if is_transitioning:
            now = pygame.time.get_ticks()
            progress = (now - transition_start) / TRANSITION_DURATION
            progress = min(1, progress)
            if progress == 1:
                is_transitioning = False
        else:
            progress = 1.0

        if moving:
            x = x1 + (x2 - x1) * progress + dx + fx
            y = y1 + (y2 - y1) * progress + dy + fy
            frame = get_frame(frames[1], time, drone)
        else:
            x = x2 + dx + fx
            y = y2 + dy + fy
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
    """
    Draw a pulsing glow effect around a zone.

    Used for start and end zones to visually
    highlight them.

    The glow expands and fades based on the pulse value.

    Args:
        values (RenderData):
            Layout values used for rendering.

        screen (pygame.Surface):
            Main rendering surface.

        rect (pygame.Rect):
            Zone rectangle.

        color (tuple[int, int, int]):
            RGB glow color.

        pulse (float):
            Animation phase between 0 and 1.

    Returns:
        None
    """
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
