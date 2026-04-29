import pygame
from .map_model import Map
from .draw_helper import compute_layout, add_turn_zero, load_animations
from .draw_methods import (draw_connections, draw_drones,
                           draw_zones, draw_turn, draw_commands)


def display_map(map_obj: Map,
                drones_table: dict[int, dict[str, str]]) -> None:
    """
    Display the interactive simulation window for the drone map.

    Renders the map structure, zones, connections, drone positions,
    turn information, and animation states using Pygame.

    Supports both automatic playback and manual turn navigation.

    Controls:
        SPACE  -> Play / Pause simulation
        RIGHT  -> Advance one turn manually
        LEFT   -> Go back one turn manually
        S      -> Stop playback and reset to turn 0
        ESC    -> Quit simulation

    Behavior:
        - During autoplay, drones animate movement between turns.
        - During manual navigation (LEFT/RIGHT), drones instantly
          change position and remain in idle animation.
        - Reaching the final turn automatically pauses playback.

    Args:
        map_obj (Map):
            Parsed map containing all zones, connections,
            and rendering information.

        drones_table (dict[int, dict[str, str]]):
            Simulation table where:
                key   -> turn number
                value -> dictionary of drone positions

            Example:
                {
                    1: {"D1": "zone_a", "D2": "zone_b"},
                    2: {"D1": "zone_c", "D2": "zone_b"},
                }

    Returns:
        None
    """
    is_playing = False
    animate_transition = False
    is_transitioning = False
    current_turn = 0
    transition_start = 0
    max_turn = max(drones_table)
    last_update = 0
    TURN_DELAY = 1000

    pygame.init()
    screen = pygame.display.set_mode((1080, 900))
    pygame.display.set_caption("Drone Map")
    width, height = screen.get_size()

    values = compute_layout(map_obj, width, height)
    drones_table = add_turn_zero(map_obj, drones_table)

    clock = pygame.time.Clock()
    fontplay = pygame.font.SysFont("arial", 48)
    fontpause = pygame.font.SysFont("arial", 28)
    fonts = fontpause, fontplay
    small_font = pygame.font.Font(None, 24)

    frames = load_animations("assets/idle.png",
                             "assets/walk.png", 4)

    running = True

    while running:
        screen.fill((25, 25, 28))
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_ESCAPE or
                   event.key == pygame.K_q):
                    running = False

                elif event.key == pygame.K_SPACE:
                    if current_turn == max_turn:
                        current_turn = 0
                        last_update = now
                    is_playing = not is_playing

                elif (event.key == pygame.K_RIGHT or
                      event.key == pygame.K_d):
                    current_turn = min(current_turn + 1, max_turn)
                    animate_transition = False
                    is_transitioning = False

                elif (event.key == pygame.K_LEFT or
                      event.key == pygame.K_a):
                    current_turn = max(current_turn - 1, 0)
                    animate_transition = False
                    is_transitioning = False

                elif event.key == pygame.K_s:
                    current_turn = 0
                    is_playing = False

        draw_connections(screen, map_obj, values)
        draw_zones(screen, map_obj, values, now)

        if is_playing and now - last_update > TURN_DELAY:
            current_turn += 1
            last_update = now
            animate_transition = True
            is_transitioning = True
            transition_start = now

        if current_turn == max_turn:
            current_turn = max_turn
            is_playing = False

        transition_values = (transition_start, animate_transition,
                             is_transitioning)

        draw_drones(screen, map_obj, values, drones_table, current_turn,
                    frames, small_font, transition_values)

        status = "▶" if is_playing else "▎▎"
        draw_turn(screen, fonts, current_turn, max_turn, status)
        draw_commands(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
