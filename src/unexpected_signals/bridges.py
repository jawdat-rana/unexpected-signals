"""Parse NDW's bridge openings feed (planningsfeed_brugopeningen) into rows.

Each situation record describes one opening, planned or current. Snapshots are
taken repeatedly, so a record is seen many times; `merge` keeps one row per
record and tracks when it was first and last seen. That lets us estimate
actual openings even though the feed itself only shows the present.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import IO

from .datex import iter_elements, local, text_of, to_float, xsi_type


@dataclass
class BridgeRecord:
    situation_id: str
    record_id: str
    version: str
    record_type: str
    management_type: str | None
    validity_status: str | None
    probability: str | None
    start_time: str | None
    end_time: str | None
    version_time: str | None
    latitude: float | None
    longitude: float | None
    first_seen: str = ""
    last_seen: str = ""

    @property
    def key(self) -> tuple[str, str]:
        return (self.situation_id, self.record_id)

    def as_row(self) -> dict[str, object]:
        return asdict(self)


COLUMNS = [f.name for f in fields(BridgeRecord)]


def parse(source: IO[bytes], fetched_at: str) -> list[BridgeRecord]:
    records: list[BridgeRecord] = []
    for situation in iter_elements(source, "situation"):
        situation_id = situation.get("id", "")
        for rec in situation.iter():
            if local(rec.tag) != "situationRecord":
                continue
            records.append(
                BridgeRecord(
                    situation_id=situation_id,
                    record_id=rec.get("id", ""),
                    version=rec.get("version", ""),
                    record_type=xsi_type(rec),
                    management_type=text_of(rec, "generalNetworkManagementType"),
                    validity_status=text_of(rec, "validityStatus"),
                    probability=text_of(rec, "probabilityOfOccurrence"),
                    start_time=text_of(rec, "overallStartTime"),
                    end_time=text_of(rec, "overallEndTime"),
                    version_time=text_of(rec, "situationRecordVersionTime"),
                    latitude=to_float(text_of(rec, "latitude")),
                    longitude=to_float(text_of(rec, "longitude")),
                    first_seen=fetched_at,
                    last_seen=fetched_at,
                )
            )
    return records


def merge(existing: list[dict[str, str]], new: list[BridgeRecord]) -> list[dict[str, object]]:
    """Upsert `new` snapshot records into `existing` rows.

    The newest values win, except `first_seen`, which keeps the earliest time.
    """
    by_key: dict[tuple[str, str], dict[str, object]] = {
        (row["situation_id"], row["record_id"]): dict(row) for row in existing
    }
    for rec in new:
        row = rec.as_row()
        old = by_key.get(rec.key)
        if old is not None and old.get("first_seen"):
            row["first_seen"] = old["first_seen"]
        by_key[rec.key] = row
    return sorted(by_key.values(), key=lambda r: (str(r["start_time"] or ""), str(r["record_id"])))
