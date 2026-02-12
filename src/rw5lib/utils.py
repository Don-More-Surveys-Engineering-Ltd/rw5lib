import datetime
import sqlite3
from pathlib import Path
from typing import overload


def parse_std_params_line(line: str) -> dict[str, str]:
    """Return dict of params from record.

    Standard record:
    GPS,PN5050,LA45.502033173001,LN-66.064406766459,EL-13.312712,--SMFD/DMSE 2024
    Comma seperated params, with 2 char prefix as name of record.
    In the above record, PN is a param and its value is 5050
    """
    return {param[:2]: param[2:].strip() for param in line.split(",")[1:]}


def parse_rw5_format_datetime(date: str, time: str, tzinfo: datetime.tzinfo):
    """Parse an rw5 formatted datetime.

    Example (from JB record):
        DT08-31-2023,TM07:54:46
    """
    fmt = "%m-%d-%Y %H:%M:%S"
    dt = datetime.datetime.strptime(f"{date} {time}", fmt)  # noqa: DTZ007
    return dt.replace(tzinfo=tzinfo)


def get_crdb_coordinate(point_id: str, crdb_path: Path) -> tuple[float, float, float]:
    """Retieves a shot from the crdb file by point id.

    Returns an RW5 row based off of db record.

    Raises ValueError if no row found.
    """  # noqa: DOC201, DOC501
    crdb_connection = sqlite3.connect(crdb_path)
    crdb_connection.row_factory = sqlite3.Row
    cursor = crdb_connection.cursor()
    crdb_query = cursor.execute("SELECT * FROM Coordinates WHERE P like ?", (point_id,))
    crdb_row: sqlite3.Row = crdb_query.fetchone()

    # skip if no crdbrow
    if not crdb_row or crdb_row["E"] is None or crdb_row["N"] is None:
        msg = f"CRDB has no shot with point id {point_id}."
        raise ValueError(msg)

    return (
        float(crdb_row["E"]),
        float(crdb_row["N"]),
        float(crdb_row["Z"]),
    )


@overload
def dms_to_dd(dms: tuple[float, float, float]) -> float: ...


@overload
def dms_to_dd(dms: str) -> float: ...


def dms_to_dd(dms: tuple[float, float, float] | str) -> float:
    """Degrees minutes seconds to decimal degrees."""
    if isinstance(dms, str):
        d, ms = dms.split(".", maxsplit=1)
        d = float(d)
        m = float(ms[:2])
        s = float(ms[2:].ljust(4, "0")) / 100
        return dms_to_dd((d, m, s))
    return dms[0] + dms[1] / 60 + dms[2] / 3600
