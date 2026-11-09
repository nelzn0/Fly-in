*This project has been created as part of the 42 curriculum by nda-roch.*

## Description

Fly-in is a drone routing system. A fleet of drones has to fly from a start zone to an end zone through a network of zones and connections. The goal is to get every drone to the end in as few simulation turns as possible, while following the rules from the subject.

Each turn, every drone can move to a connected zone, wait, or fly along a connection toward a restricted zone (that takes two turns). A zone can only hold a limited number of drones, and a connection can only carry a limited number of drones at the same time.

The program reads a map file, plans a path for each drone, runs the simulation turn by turn and then shows the result. You can see it as plain text in the terminal, or in a pygame window.

## Instructions

### Prerequisites

- Python 3.10+
- uv package manager

### Installation

```bash
make install
```

This runs `uv sync`, which installs flake8, mypy, pygame and pytest.

### Running the Program

```bash
make run
```

This runs the default map, `maps/easy/01_linear_path.txt`. To use another map:

```bash
make run MAP_FILE=maps/hard/01_maze_nightmare.txt
```

Or run the script directly:

```bash
uv run python main.py <map_file>
```

After the simulation runs, the program asks which view you want: `1` for the terminal, `2` for the graphical view.

**Other Makefile rules:**
- `make debug`: runs the program in pdb
- `make clean`: removes `__pycache__` and `.mypy_cache`
- `make lint`: runs flake8 and mypy
- `make lint-strict`: runs flake8 and mypy with `--strict`

**Tests:** a few crash tests live in `tests/`. Run them with `uv run pytest`.

### Example

Map file `maps/easy/01_linear_path.txt`:

```
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Terminal output (after choosing `1`):

```
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

Each line is one turn. Each move is written as `D<id>-<zone>`. A drone that is flying toward a restricted zone is written as `D<id>-<hub1>-<hub2>`, which is the connection it is on.

## Map Format

- `nb_drones: <number>` sets how many drones to send. It should be the first line.
- `start_hub:` and `end_hub:` define the only start and end zones. Each map needs exactly one of each.
- `hub:` defines a normal zone. The format is `name x y [metadata]`.
- `connection: hub1-hub2 [metadata]` links two zones that already exist. Zone names cannot contain `-` or spaces.
- Metadata is optional and goes in brackets:
  - For zones, any order: `zone=normal|restricted|priority|blocked` (default `normal`), `color=<name>` (default none, only used for the display), `max_drones=<number>` (default 1, ignored on start and end).
  - For connections: `max_link_capacity=<number>` (default 1).
- Lines that start with `#` are comments.

If the map is wrong, the program prints the line number and the reason, then stops.

## Algorithm Explanation

The program works in two steps: first it plans a path for every drone, then it runs the turns.

### Step 1: Pathfinding

The pathfinder is a Dijkstra-style search, written by hand. It always takes the cheapest zone it has not settled yet, and stops when it reaches the end. No graph library is used, because the subject forbids it.

The cost of stepping into a zone is:
- `normal`: 1
- `restricted`: 2
- `priority`: 0.5, so the search prefers these zones (the real move still takes 1 turn)
- `blocked`: never entered, the search skips it

On top of that, every zone has a **load**. Each time a drone's path goes through a zone, that zone's load goes up by 0.5 (`HUB_PENALTY`). So the next drone sees a busy zone as more expensive, and it tends to take a different route. This is what spreads the drones over the map.

The drones are planned one after another in `Simulation.drone_paths()`, and the paths are only calculated once, before the first turn.

[TODO: complexity, see subject VII.1]

### Step 2: Turn Simulation

`Simulation.run()` loops over the turns until every drone is delivered. On each turn:

1. The drones are checked in order (D1, D2, ...).
2. A drone that is flying toward a restricted zone lands in that zone.
3. Any other drone tries to step to the next zone on its plan. It can move only if:
   - the zone has room (`_can_enter_zone`). The drones already inside count, and so do the drones flying toward it. The start and end zones have no limit.
   - the connection has room (`_can_use_link`). The drones on it count, and so do the moves already made on it this turn.
4. If a drone can't move, it waits.

A restricted zone works in two turns. On the first turn the drone goes into the connection, and the space in the zone is reserved right away. On the next turn it lands.

If no drone can move in a turn, the simulation stops with an error, because it would never finish.

### Map Reading

`Parser` reads the file line by line. It splits each line at the first colon, then checks the prefix and the values. Every error includes the line number. Connections are stored once per pair of zones, so `a-b` and `b-a` count as the same connection.

## Design Decisions

- **One file per job.** The parser, the models, the pathfinder, the simulation and the output are separate files, so each part can be read and tested on its own.
- **Plan first, then move.** All paths are planned before the turns start. The simulation only has to follow them and check the capacity rules.
- **Dataclasses for the data.** `Hub`, `Connection`, `Drone` and `ParsedMap` are dataclasses. They only hold data, and the logic lives in the other classes.
- **Errors with line numbers.** `FlyInError` takes an optional line number. `ParseError` is for map mistakes, and `SimulationError` is for problems during the run.
- **Priority is a preference, not a shortcut.** The pathfinder uses 0.5 so it likes priority zones, but the simulation still counts 1 turn for them.

## Visual Representation

**Terminal:** one line per turn, with every move of that turn. This is the format from the subject, and it is easy to copy or compare between runs.

**Graphical view (pygame):**
- Zones are circles, in the color from the map (white if there is none). Each zone shows its name, its zone type, and the drones inside it.
- Connections are green lines. A connection that has drones on it shows them too.
- Drones are small colored circles. The color depends on the drone number.
- The top bar shows the current turn.
- The turns advance on their own, one turn every 0.7 seconds.

[TODO: update this part once the playback choice (automatic or space bar) is decided]

## Performance

Results from running the program on the provided maps. The subject targets are in the last column.

| Map | Drones | Turns | Subject target |
|-----|--------|-------|----------------|
| easy/01_linear_path | 2 | 4 | 6 |
| easy/02_simple_fork | 4 | 4 | 8 |
| easy/03_basic_capacity | 4 | 4 | 6 |
| medium/01_dead_end_trap | 5 | 8 | 12 |
| medium/02_circular_loop | 6 | 15 | 15 |
| medium/03_priority_puzzle | 5 | 7 | 12 |
| hard/01_maze_nightmare | 8 | 13 | 30 |
| hard/02_capacity_hell | 12 | 16 | 35 |
| hard/03_ultimate_challenge | 15 | 28 | 45 |
| challenger/01_the_impossible_dream | 25 | 49 | 45 (record, optional) |

The Impossible Dream is not solved under the 45-turn record yet.

[TODO: check every output by hand against the rules, and measure the run time]

## Known Limitations

- The terminal output has no colors yet.
- The pathfinder plans each drone once, so it does not look ahead at the drones planned after it.
- [TODO: list anything else found during the review]

## Resources

### References

- [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm) - the idea behind the pathfinder
- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html) - the data classes in `models.py` and `drone.py`
- [PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/) - the docstring rules
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) - the docstring layout (`Args:`, `Returns:`, `Raises:`)
- [pygame documentation](https://www.pygame.org/docs/) - the graphical view
- [mypy documentation](https://mypy.readthedocs.io/) - type checking
- [flake8 documentation](https://flake8.pycqa.org/) - style checking

### AI Usage

[TODO: describe which tasks and which parts of the project AI helped with]

## Project Files

- `main.py`: entry point. Reads the arguments, runs everything, and asks for the view.
- `parser.py`: reads the map file and checks it.
- `models.py`: the `Hub` and `Connection` data classes.
- `pathfinder.py`: finds the cheapest path for a drone.
- `drone.py`: the `Drone` data class.
- `simulation.py`: plans the paths and runs the turns.
- `terminaloutput.py`: prints the turns to the terminal.
- `renderer.py`: the pygame graphical view.
- `exceptions.py`: the error classes.
