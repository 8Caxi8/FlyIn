*This project has been created as part of the 42 curriculum by dansimoe.*

# Fly-in — Drone Routing Simulator

## Description

Fly-in is a drone fleet routing simulator built as part of the 42 curriculum. The goal
is to move all drones from a start hub to an end hub across a network of connected zones
in the fewest possible simulation turns.

The program reads a custom map file format defining zones, connections, and constraints,
then computes optimal paths using a BFS-based pathfinding algorithm, simulates the
drone movements turn by turn respecting all capacity and movement rules, and renders
the result both as terminal output and as an interactive Pygame visualization.

## Instructions

### Requirements

- Python 3.10 or later
- pip or any compatible package manager

### Installation

```bash
make install
```

### Running

```bash
make run
```

To load a specific map:
```bash
uv run python3 -m src --input <map_path>
```

To disable the graphical interface:
```bash
uv run python3 -m src --no-gui
```

If no `--input` is provided, the program falls back to `default.txt`.

### Other Makefile targets

- `make lint` — run flake8 and mypy type checking
- `make lint-strict` — run mypy with `--strict`
- `make debug` — run with Python's built-in debugger (pdb)
- `make clean` — remove `__pycache__` and `.mypy_cache`

## Algorithm

### Pathfinding

Paths are found using a custom BFS implementation (no external graph libraries are
used). The BFS explores the zone graph from the start hub, skipping blocked zones and
already-visited nodes within a given path to avoid cycles.

Up to N candidate paths are collected (default: 5, configurable). A pruning mode is
also available for fast solvability checking, which returns on the first valid path
found using a visited-depth dictionary to eliminate redundant expansions.

A depth limit of 50 is enforced, with a fallback to 60 for complex maps. Maps with no
reachable path within this limit are rejected at parse time.

### Drone Assignment

Drones are assigned sequentially to paths using a greedy simulation strategy:

1. For each drone, every candidate path is simulated against the current capacity
   reservations.
2. The path with the lowest predicted finish turn is selected. Ties are broken by
   the number of priority zones in the path, and randomly when all else is equal
   (to spread drones across equivalent paths for better visual distribution).
3. Once a path is selected, the drone's turn-by-turn positions are committed to a
   unified capacity table that tracks both zone occupancy and edge traversal per turn.

### Capacity and Movement Rules

- Each zone has a `max_drones` limit (default: 1). Start and end zones are exempt.
- Each connection has a `max_link_capacity` limit (default: 1).
- Both are enforced via a single unified `capacity_table` keyed by turn number,
  using zone names for occupancy and canonical `"A-B"` strings for edge traversal.
- Restricted zones cost 2 turns: the drone occupies the edge on turn T and arrives
  at the zone on turn T+1. It cannot wait on the edge.
- Blocked zones are entirely excluded from pathfinding.
- Priority zones cost 1 turn and are preferred during path selection.

### Complexity

- BFS path discovery: O(V + E) per path, repeated up to N times.
- Drone assignment: O(D × P × L) where D is drone count, P is path count, and L is
  maximum path length including wait steps.
- Capacity table lookups: O(1) per turn per zone/edge.

Paths are computed once and reused across all drone assignments (no recalculation).
The capacity table grows linearly with the number of turns and active zones.

## Visual Representation

The Pygame interface renders the simulation interactively with the following features:

- **Zone nodes** are drawn as colored rectangles using the color metadata from the
  map file. Start and end zones pulse with a glow effect.
- **Connections** are rendered as lines between zone centers.
- **Drones** are rendered as animated sprites with idle and movement animations loaded
  from spritesheets. Each drone has a stable hash-based positional offset to avoid
  overlap, and a subtle floating animation while idle.
- **Smooth transitions** animate drone movement between turns during autoplay.
- **Turn counter** is displayed at the top of the screen.

### Controls

| Key | Action |
|-----|--------|
| `SPACE` | Play / Pause |
| `D` / `→` | Next turn |
| `A` / `←` | Previous turn |
| `S` | Reset to turn 0 |
| `Q` / `ESC` | Quit |

## Resources

### References

- [BFS — Wikipedia](https://en.wikipedia.org/wiki/Breadth-first_search)
- [Pygame documentation](https://www.pygame.org/docs/)
- [Pydantic documentation](https://docs.pydantic.dev/)

### AI Usage

AI was used during this project for the following:

- Code review and debugg
- Reviewing docstrings and suggesting improvements to clarity and completeness

All AI-generated suggestions were reviewed and validated before being
integrated. The core architecture, algorithms, and implementation decisions were made
independently.