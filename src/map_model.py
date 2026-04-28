from pydantic import BaseModel, Field, model_validator
from pydantic_core import PydanticCustomError as Pe
from enum import Enum
from typing import Any


class MapError(Exception):
    pass


class ZoneType(str, Enum):
    """Enumeration of valid zone types and their movement costs.

    Attributes:
        NORMAL: Standard zone, costs 1 turn to enter.
        BLOCKED: Inaccessible zone, cannot be entered.
        RESTRICTED: Sensitive zone, costs 2 turns to enter.
        PRIORITY: Preferred zone, costs 1 turn and is prioritized
                  in pathfinding.
    """
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone(BaseModel):
    """Represents a single zone (node) in the drone network.

    Attributes:
        name: Unique zone identifier. Cannot contain dashes or spaces.
        x: Integer x-coordinate on the map grid.
        y: Integer y-coordinate on the map grid.
        zone_type: Movement cost/behavior type of this zone.
        color: Optional display color for visual representation.
        max_drones: Maximum number of drones that can occupy this
                    zone simultaneously.
    """
    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str | None = None
    max_drones: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def validate_name(self) -> "Zone":
        """Ensure the zone name contains no dashes or spaces.

        Returns:
            The validated Zone instance.

        Raises:
            PydanticCustomError: If the name contains dashes or spaces.
        """
        if "-" in self.name or " " in self.name:
            raise Pe("zone_name_error",
                     "[ERROR]: Zone names can use any valid characters "
                     f"but dashes and spaces '{self.name}'")

        return self

    def __repr__(self) -> str:
        """Return a string representation of the zone.

        Returns:
            The zone name.
        """
        return f"{self.name}"

    def to_dict(self) -> dict[str, Any]:
        """Serialize the zone to a dictionary for use in Map storage.

        Returns:
            A dict with keys: position, zone_type, color, max_drones.
        """
        return {
            "position": (self.x, self.y),
            "zone_type": self.zone_type,
            "color": self.color,
            "max_drones": self.max_drones,
        }


class Connection(BaseModel):
    """Represents a bidirectional edge between two zones.

    Attributes:
        zone1: Name of the first zone.
        zone2: Name of the second zone.
        max_link_capacity: Maximum number of drones that can traverse
                           this connection simultaneously.
    """
    zone1: str
    zone2: str
    max_link_capacity: int = Field(default=1, ge=1)

    def __repr__(self) -> str:
        """Return a string representation of the connection.

        Returns:
            A dash-separated string of the two zone names.
        """
        return f"{self.zone1}-{self.zone2}"


class Map:
    """Represents the full drone network graph.

    Stores zones, connections, adjacency data, and capacity
    constraints. Acts as the central data structure passed through
    parsing, pathfinding, and simulation.

    Attributes:
        drones: Number of drones to route.
        start_zone: Name of the start hub zone.
        end_zone: Name of the end hub zone.
        zones: Maps zone names to their metadata dicts.
        connections: Set of canonical (sorted) zone name pairs.
        connection_capacity: Maps connection tuples to their capacity.
        adjacency: Maps each zone name to its list of neighbors.
    """
    def __init__(self, nb_drones: str) -> None:
        """Initialize an empty map with a given drone count.

        Args:
            nb_drones: String representation of the number of drones.

        Raises:
            MapError: If nb_drones is not a positive integer.
        """
        self.set_drones(nb_drones)
        self.start_zone: str | None = None
        self.end_zone: str | None = None
        self.zones: dict[str, dict[str, Any]] = {}
        self.connections: set[tuple[str, str]] = set()
        self.connection_capacity: dict[tuple[str, str], int] = {}
        self.adjacency: dict[str, list[str]] = {}

    def set_drones(self, nb_drones: str) -> None:
        """Parse and validate the drone count from a string.

        Args:
            nb_drones: String representation of the number of drones.

        Raises:
            MapError: If the value is not a positive integer.
        """
        try:
            if int(nb_drones) <= 0:
                raise ValueError(f"{nb_drones} "
                                 "must be a positive integer!")
            else:
                self.drones = int(nb_drones)
        except ValueError as e:
            raise MapError(str(e))

    def add_zone(self, zone: Zone) -> None:
        """Add a zone to the map.

        Args:
            zone: The Zone instance to add.

        Raises:
            MapError: If the zone name or coordinates are duplicated.
        """
        if zone.name in self.zones:
            raise MapError(f"{zone.name} is duplicated!")
        if (zone.x, zone.y) in {szone["position"]
                                for szone in self.zones.values()}:
            raise MapError(f"{(zone.x, zone.y)} is duplicated!")
        self.zones[zone.name] = zone.to_dict()
        self.adjacency[zone.name] = []

    def add_connection(self, connection: Connection) -> None:
        """Add a bidirectional connection between two zones.

        Canonicalizes the zone pair (alphabetical order) before
        storing to prevent duplicate connections in either direction.

        Args:
            connection: The Connection instance to add.

        Raises:
            MapError: If the connection is duplicated or references
                      an undefined zone.
        """
        a, b = connection.zone1, connection.zone2

        zones = (a, b) if a < b else (b, a)

        if zones in self.connections:
            raise MapError("[ERROR]: "
                           f"Duplicated connection {connection}")

        invalid_zone = self.check_zones(a, b)
        if invalid_zone is None:
            self.connections.add(zones)
            self.connection_capacity[zones] = connection.max_link_capacity
            self.adjacency[a].append(b)
            self.adjacency[b].append(a)

            return

        raise MapError(
            "[ERROR]: Invalid connection "
            f"{a}-{b}: "
            f"{invalid_zone} is not a valid zone!")

    def set_start_zone(self, zone: Zone) -> None:
        """Register a zone as the unique start hub.

        Args:
            zone: The Zone instance to set as start.

        Raises:
            MapError: If a start zone has already been defined.
        """
        if self.start_zone:
            raise MapError("There must be only one start_hub: "
                           f"{self.start_zone} incompatible with "
                           f"{zone}")

        self.add_zone(zone)
        self.start_zone = zone.name

    def set_end_zone(self, zone: Zone) -> None:
        """Register a zone as the unique end hub.

        Args:
            zone: The Zone instance to set as end.

        Raises:
            MapError: If an end zone has already been defined.
        """
        if self.end_zone:
            raise MapError("There must be only one end_hub: "
                           f"{self.end_zone} incompatible with "
                           f"{zone}")

        self.add_zone(zone)
        self.end_zone = zone.name

    def check_zones(self, zone1: str, zone2: str) -> None | str:
        """Check that both zone names exist in the map.

        Args:
            zone1: Name of the first zone.
            zone2: Name of the second zone.

        Returns:
            The name of the first invalid zone found, or None if
            both zones are valid.
        """
        if zone1 not in self.zones:
            return zone1

        if zone2 not in self.zones:
            return zone2

        return None

    def check_map(self) -> None:
        """Validate that the map has zones, a start hub, and an end hub.

        Raises:
            MapError: If the map has no zones, no start hub, or no
                      end hub.
        """
        if not self.zones:
            raise MapError("There are no zones!")

        if self.start_zone is None:
            raise MapError("Missing start_hub!")

        if self.end_zone is None:
            raise MapError("Missing end_hub!")
