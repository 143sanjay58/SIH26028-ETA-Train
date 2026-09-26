"""
Read-only in-memory catalogue of the validated SIH26028 train dataset.

The catalogue indexes backend/app/sih_eta/ml_ready_segments_final.csv once and
keeps it in memory so train-number lookups and route reconstruction never re-read
the CSV per request. The CSV itself stays untouched.

The catalogue is a companion data source to railway.db: application/identity/
operational/simulation data lives in the DB, while historical/model train
catalogue data lives here. It never writes to railway.db.
"""
import os
import threading
from typing import Dict, List, Optional

import pandas as pd

_SIH_ETA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sih_eta",
)
CATALOGUE_CSV_PATH = os.path.join(_SIH_ETA_DIR, "ml_ready_segments_final.csv")

CATALOGUE_SOURCE = "SIH_CATALOGUE"


def _normalize(train_number: str) -> str:
    normalized = str(train_number).strip().lstrip("0")
    return normalized if normalized else "0"


def _is_empty(value) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _s(value) -> Optional[str]:
    return None if _is_empty(value) else str(value).strip()


def _i(value) -> Optional[int]:
    return None if _is_empty(value) else int(value)


def _f(value) -> Optional[float]:
    return None if _is_empty(value) else float(value)


def _b(value) -> Optional[bool]:
    return None if _is_empty(value) else bool(value)


class SIHTrainCatalogue:
    def __init__(self, csv_path: str = CATALOGUE_CSV_PATH):
        self.csv_path = csv_path
        self._rows_by_number: Optional[Dict[str, pd.DataFrame]] = None
        self._number_by_norm: Dict[str, str] = {}
        self._route_cache: Dict[str, List[Dict]] = {}
        self._total_trains = 0

    @property
    def loaded(self) -> bool:
        return self._rows_by_number is not None

    @property
    def unique_train_count(self) -> int:
        return self._total_trains

    def load(self) -> "SIHTrainCatalogue":
        if self.loaded:
            return self

        df = pd.read_csv(self.csv_path)
        df["train_number"] = df["train_number"].astype(str).str.strip()

        rows: Dict[str, pd.DataFrame] = {}
        norms: Dict[str, str] = {}
        for number, group in df.groupby("train_number", sort=True):
            rows[number] = group.sort_values("route_order")
            norms[_normalize(number)] = number

        self._rows_by_number = rows
        self._number_by_norm = norms
        self._total_trains = len(rows)
        return self

    def _resolved_number(self, train_number: str) -> Optional[str]:
        if not self.loaded:
            return None
        exact = str(train_number).strip()
        if exact in self._rows_by_number:
            return exact
        return self._number_by_norm.get(_normalize(exact))

    def has_train(self, train_number: str) -> bool:
        return self._resolved_number(train_number) is not None

    def get_train(self, train_number: str) -> Optional[Dict]:
        number = self._resolved_number(train_number)
        if number is None:
            return None

        route = self.get_route(number)
        if not route:
            return None

        first = route[0]
        last = route[-1]
        return {
            "train_number": number,
            "train_name": None,
            "origin_station": first["from_station"],
            "origin_station_name": first["from_station_name"] or first["from_station"],
            "destination_station": last["to_station"],
            "destination_station_name": last["to_station_name"] or last["to_station"],
            "route_segments": len(route),
            "has_route": True,
            "source": CATALOGUE_SOURCE,
        }

    def get_route(self, train_number: str) -> Optional[List[Dict]]:
        number = self._resolved_number(train_number)
        if number is None:
            return None

        cached = self._route_cache.get(number)
        if cached is not None:
            return cached

        group = self._rows_by_number[number]
        records = []
        for _, r in group.iterrows():
            records.append(
                {
                    "train_number": _s(r.get("train_number")),
                    "route_order": _i(r.get("route_order")),
                    "from_station": _s(r.get("from_station")),
                    "from_station_name": _s(r.get("from_station_name")),
                    "from_station_canonical": _s(r.get("from_station_canonical")),
                    "to_station": _s(r.get("to_station")),
                    "to_station_name": _s(r.get("to_station_name")),
                    "to_station_canonical": _s(r.get("to_station_canonical")),
                    "from_arrival": _s(r.get("from_arrival")),
                    "from_departure": _s(r.get("from_departure")),
                    "to_arrival": _s(r.get("to_arrival")),
                    "to_departure": _s(r.get("to_departure")),
                    "from_day": _i(r.get("from_day")),
                    "to_day": _i(r.get("to_day")),
                    "scheduled_run_minutes": _f(r.get("scheduled_run_minutes")),
                    "is_overnight": _b(r.get("is_overnight")),
                    "is_long_segment": _b(r.get("is_long_segment")),
                    "is_very_long_segment": _b(r.get("is_very_long_segment")),
                    "same_canonical_station": _b(r.get("same_canonical_station")),
                    "status": _s(r.get("status")),
                }
            )

        self._route_cache[number] = records
        return records

    def search_trains(self, query: str, limit: int = 50) -> List[str]:
        if not self.loaded:
            return []

        q = str(query).strip()
        results: List[str] = []
        if not q:
            return results

        for number in self._rows_by_number:
            normalized = self._number_by_norm.get(_normalize(number), "")
            if q in number or q in normalized:
                results.append(number)
                if len(results) >= limit:
                    break
        return results


_catalogue: Optional[SIHTrainCatalogue] = None
_catalogue_lock = threading.Lock()


def get_catalogue() -> SIHTrainCatalogue:
    global _catalogue
    if _catalogue is None:
        with _catalogue_lock:
            if _catalogue is None:
                _catalogue = SIHTrainCatalogue().load()
    return _catalogue