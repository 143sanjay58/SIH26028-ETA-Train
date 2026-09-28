"""
Read-only, process-cached aggregation of the SIH catalogue train routes into a
deduplicated railway-network representation.

Companion to ``sih_catalogue.py``: the catalogue answers per-train lookups,
while this service collapses every train's ordered segments into a single
network graph (nodes + directed edges) for the Railway Map. Both modules read
``ml_ready_segments_final.csv`` and ``stations.json``; neither ever writes to
``railway.db``.

The expensive aggregation runs once per process and is cached in memory.
"""
import json
import os
import threading
from typing import Dict, List, Optional, Tuple

import pandas as pd

from backend.app.schemas.network import NetworkStation
from backend.app.services.sih_catalogue import CATALOGUE_CSV_PATH

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
STATIONS_JSON_PATH = os.path.join(_REPO_ROOT, "stations.json")


class NetworkGraph:
    def __init__(self, stations: List[NetworkStation], edges: List[List[str]]):
        self.stations = stations
        self.edges = edges


_network_lock = threading.Lock()
_network_cache: Optional[NetworkGraph] = None


def _load_station_coordinates() -> Dict[str, Tuple[str, float, float]]:
    """Return {CODE.upper(): (name, latitude, longitude)} from stations.json.

    Only features with a valid Point geometry and finite coordinates are kept.
    Missing/unreadable stations.json yields an empty map and is never fatal:
    edges without coordinates on either endpoint are simply skipped.
    """
    coords: Dict[str, Tuple[str, float, float]] = {}
    if not os.path.exists(STATIONS_JSON_PATH):
        return coords

    try:
        with open(STATIONS_JSON_PATH, "r", encoding="utf-8") as fh:
            feature_collection = json.load(fh)
    except (OSError, ValueError):
        return coords

    features = feature_collection.get("features", []) if isinstance(feature_collection, dict) else []
    for feature in features:
        properties = feature.get("properties") or {}
        code = str(properties.get("code") or "").strip().upper()
        geometry = feature.get("geometry") or {}
        if not code or geometry.get("type") != "Point":
            continue
        coordinate = geometry.get("coordinates")
        if not isinstance(coordinate, list) or len(coordinate) < 2:
            continue
        if not all(isinstance(v, (int, float)) for v in coordinate[:2]):
            continue
        longitude, latitude = float(coordinate[0]), float(coordinate[1])
        if not (abs(latitude) <= 90.0 and abs(longitude) <= 180.0):
            continue
        coords[code] = (str(properties.get("name") or code), latitude, longitude)

    return coords


def _build_network() -> NetworkGraph:
    df = pd.read_csv(CATALOGUE_CSV_PATH)

    string_columns = [
        "from_station",
        "from_station_name",
        "to_station",
        "to_station_name",
        "from_station_canonical",
        "to_station_canonical",
    ]
    for column in string_columns:
        df[column] = df[column].fillna("").astype(str).str.strip()

    df["from_station"] = df["from_station"].str.upper()
    df["to_station"] = df["to_station"].str.upper()

    segments = df[df["from_station"] != ""][df["to_station"] != ""]

    # Drop zero-length segments between the same physical station
    # (e.g. station renames where only the code differs).
    segments = segments[
        ~(
            (segments["from_station_canonical"] != "")
            & (segments["from_station_canonical"] == segments["to_station_canonical"])
        )
    ]

    edges_df = (
        segments[["from_station", "to_station"]]
        .drop_duplicates()
        .sort_values(["from_station", "to_station"])
        .reset_index(drop=True)
    )

    coords = _load_station_coordinates()

    # Keep only edges where both endpoints have valid coordinates.
    edges_df["from_ok"] = edges_df["from_station"].isin(coords)
    edges_df["to_ok"] = edges_df["to_station"].isin(coords)
    edges_df = edges_df[edges_df["from_ok"] & edges_df["to_ok"]]
    edges_df = edges_df[["from_station", "to_station"]]

    edge_pairs: List[List[str]] = [[row["from_station"], row["to_station"]] for _, row in edges_df.iterrows()]

    used_codes = {code for pair in edge_pairs for code in pair}

    # Most common catalogue name per code (from endpoint names on both sides).
    endpoint_names = pd.concat(
        [
            segments[["from_station", "from_station_name"]].rename(
                columns={"from_station": "code", "from_station_name": "name"}
            ),
            segments[["to_station", "to_station_name"]].rename(
                columns={"to_station": "code", "to_station_name": "name"}
            ),
        ]
    )
    endpoint_names = endpoint_names[endpoint_names["name"] != ""].drop_duplicates()
    name_by_code: Dict[str, str] = {}
    for code, group in endpoint_names.groupby("code")["name"]:
        code = str(code)
        if code in used_codes:
            name_by_code[code] = group.value_counts().index[0]

    stations: List[NetworkStation] = []
    for code in sorted(used_codes):
        coordinate = coords[code]
        stations.append(
            NetworkStation(
                code=code,
                name=name_by_code.get(code) or coordinate[0],
                latitude=coordinate[1],
                longitude=coordinate[2],
            )
        )

    return NetworkGraph(stations=stations, edges=edge_pairs)


def get_network_routes() -> NetworkGraph:
    """Return the cached deduplicated network graph, building it once."""
    global _network_cache
    if _network_cache is None:
        with _network_lock:
            if _network_cache is None:
                _network_cache = _build_network()
    return _network_cache