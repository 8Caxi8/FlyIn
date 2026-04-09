from pydantic import BaseModel, Field, model_validator
from pydantic_core import PydanticCustomError as Pe
from enum import Enum
from typing import Any


class MapError(Exception):
    pass


class ZoneType(str, Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone(BaseModel):
    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str | None = None
    max_drones: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def validate_name(self) -> "Zone":
        if "-" in self.name or " " in self.name:
            raise Pe("zone_name_error",
                     "[ERROR]: Zone names can use any valid characters "
                     f"but dashes and spaces '{self.name}'")

        return self

    def __repr__(self) -> str:
        return f"{self.name}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "position": (self.x, self.y),
            "zone_type": self.zone_type,
            "color": self.color,
            "max_drones": self.max_drones,
        }


class Connection(BaseModel):
    zone1: str
    zone2: str
    max_link_capacity: int = Field(default=1, ge=1)

    def __iter__(self):
        yield self.zone1
        yield self.zone2

    def __repr__(self) -> str:
        return f"{self.zone1}-{self.zone2}"


class Map:
    def __init__(self, nb_drones: str) -> None:
        self.set_drones(nb_drones)
        self.start_zone: str | None = None
        self.end_zone: str | None = None
        self.zones: dict[str, dict[str, Any]] = {}
        self.connections: set[tuple[str, str]] = set()
        self.connection_capacity: dict[tuple[str, str], int] = {}
        self.adjacency: dict[str, list[str]] = {}

    def set_drones(self, nb_drones: str) -> None:
        try:
            if int(nb_drones) <= 0:
                raise ValueError(f"{nb_drones} "
                                 "must be a positive integer!")
            else:
                self.drones = int(nb_drones)
        except ValueError as e:
            raise MapError(str(e))

    def add_zone(self, zone: Zone) -> None:
        if zone.name in self.zones:
            raise MapError(f"{zone.name} is duplicated!")
        if (zone.x, zone.y) in {szone["position"]
                                for szone in self.zones.values()}:
            raise MapError(f"{(zone.x, zone.y)} is duplicated!")
        self.zones[zone.name] = zone.to_dict()
        self.adjacency[zone.name] = []

    def add_connection(self, connection: Connection) -> None:
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
        if self.start_zone:
            raise MapError("There must be only one start_hub: "
                           f"{self.start_zone} incompatible with "
                           f"{zone}")

        self.add_zone(zone)
        self.start_zone = zone.name

    def set_end_zone(self, zone: Zone) -> None:
        if self.end_zone:
            raise MapError("There must be only one end_hub: "
                           f"{self.end_zone} incompatible with "
                           f"{zone}")

        self.add_zone(zone)
        self.end_zone = zone.name

    def check_zones(self, zone1: str, zone2: str) -> None | str:
        if zone1 not in self.zones:
            return zone1

        if zone2 not in self.zones:
            return zone2

        return None

    def check_map(self) -> None:
        if not self.zones:
            raise MapError("There are no zones!")

        if self.start_zone is None:
            raise MapError("Missing start_hub!")

        if self.end_zone is None:
            raise MapError("Missing end_hub!")
