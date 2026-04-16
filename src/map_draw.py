import pygame
from .map_model import Map
from .draw_helper import compute_layout, add_turn_zero, load_animations
from .draw_methods import draw_connections, draw_drones, draw_zones, draw_turn


def display_map(map_obj: Map,
                drones_table: dict[int, dict[str, str]]) -> None:
    is_playing = False
    animate_transition = False
    is_transitioning = False
    current_turn = 0
    transition_start = 0
    max_turn = max(drones_table)
    last_update = 0
    TURN_DELAY = 1000

    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Drone Map")
    width, height = screen.get_size()

    values = compute_layout(map_obj, width, height)
    drones_table = add_turn_zero(map_obj, drones_table)

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 48)
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
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    if current_turn == max_turn:
                        current_turn = 0
                        last_update = now
                    is_playing = not is_playing

                elif event.key == pygame.K_RIGHT:
                    current_turn = min(current_turn + 1, max_turn)
                    animate_transition = False
                    is_transitioning = False

                elif event.key == pygame.K_LEFT:
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

        status = "▶" if is_playing else "⏸"
        draw_turn(screen, font, current_turn, status)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
