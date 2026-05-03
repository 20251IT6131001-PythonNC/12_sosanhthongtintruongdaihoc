"""
Shared enumerations for the application.
"""
from enum import IntEnum


class RegionEnum(IntEnum):
    ASIA          = 1
    EUROPE        = 2
    NORTH_AMERICA = 3
    LATIN_AMERICA = 4
    OCEANIA       = 5
    AFRICA        = 6


REGION_LABELS: dict[int, str] = {
    RegionEnum.ASIA:          "Asia",
    RegionEnum.EUROPE:        "Europe",
    RegionEnum.NORTH_AMERICA: "North America",
    RegionEnum.LATIN_AMERICA: "Latin America",
    RegionEnum.OCEANIA:       "Oceania",
    RegionEnum.AFRICA:        "Africa",
}
