"""RW5 Record types.

All record types must be registered in RECORD_CLASSES at bottom of file to be used by interpreter.
"""

import datetime
from dataclasses import dataclass
from functools import cached_property
from typing import Any

from rw5lib.exceptions import MalformedGPSRecordError
from rw5lib.utils import parse_rw5_format_datetime, parse_std_params_line


@dataclass
class MachineState:
    """Tracks fields over multiple records."""

    instrument_height: float | None = None
    rod_height: float | None = None
    prism_applied: str | None = None
    projection: str | None = None
    equipment: str | None = None
    antenna_type: str | None = None
    rtk_method: str | None = None
    geoid_seperation_file: str | None = None
    job: str | None = None
    job_datetime: datetime.datetime | None = None


class RW5Record:
    """Single RW5 record."""

    _block: list[str]
    _prev_block: list[str] | None
    type: str
    point_id: str | None
    raw: str
    fields: dict[str, str]
    comments: list[str]
    machine_state: MachineState
    tzinfo: datetime.tzinfo

    def __init__(
        self,
        block: list[str],
        prev_block: list[str] | None,
        machine_state: MachineState,
        tzinfo: datetime.tzinfo,
    ) -> None:
        self._block = block
        self._prev_block = prev_block
        self.tzinfo = tzinfo
        self.machine_state = machine_state
        self.raw, *self.comments = [line.strip() for line in block]
        self.type = self.get_type()
        self.fields = self.get_fields()
        self.point_id = self.get_point_id()
        self.update_machine_state()

    def get_point_id(self) -> str | None:  # noqa: D102
        return None

    def get_type(self) -> str:  # noqa: D102
        return self.raw.split(",")[0]

    def get_fields(self) -> dict[str, str]:
        """Parse fields from record.

        Remarks:
            In base class, only parses the fields of the first line, as comment records are not standardized and need to be handled depending on record type.
        """
        return parse_std_params_line(self.raw)

    def update_machine_state(self) -> None:  # noqa: D102
        pass

    def __str__(self) -> str:
        return f"{self.type} {self.point_id}"


class DatedRecord(RW5Record):
    """RW5 record with date and time fields.

    Example:
        --DT07-16-2025
        --TM11:13:04

    """

    @cached_property
    def datetime(self) -> datetime.datetime | None:
        """Return datetime in local TZ."""
        date_line_match = [line.strip() for line in self.comments if line.strip().startswith("--DT")]
        # e.g. --TM11:24:29
        time_line_match = [line.strip() for line in self.comments if line.strip().startswith("--TM")]
        if date_line_match and time_line_match:
            dt_str = date_line_match[0].removeprefix("--DT")
            tm_str = time_line_match[0].removeprefix("--TM")
            return parse_rw5_format_datetime(dt_str, tm_str, self.tzinfo)
        return None


class JBRecord(RW5Record):
    """Job record. Usually the first record in the file.

    Example:
        JB,NM19194AT230830,DT08-31-2023,TM07:54:46
    """

    def update_machine_state(self):  # noqa: D102
        super().update_machine_state()
        self.machine_state.job = self.fields.get("NM")
        dt_str = self.fields.get("DT")
        tm_str = self.fields.get("TM")
        if dt_str and tm_str:
            self.machine_state.job_datetime = parse_rw5_format_datetime(dt_str, tm_str, self.tzinfo)


class BPRecord(RW5Record):
    """Base point record. May indicate change in coordinate system.

    Stubbed incase special handling needed in future.

    Example:
        BP,PN1253_BASE_1,LA45.000000000000,LN-66.000000000000,EL7.2160,AG0.0000,PA0.0000,ATAPC,SRROVER,--

    """


class BKRecord(RW5Record):
    """Parse BK (backsight) record.

    Example:
        BK,OPTEMP1,BPCP5,BS120.5809,BC120.5809
        --P.C. mm Applied: 0.0000 (Reflectorless:foresight)

    """

    @property
    def reflectorless(self):  # noqa: D102
        return "(reflectorless:foresight)" in self.comments[0].lower()


class OCRecord(RW5Record):
    """Occupy point record.

    Stubbed incase special handling needed in future.

    Example:
        OC,OPTEMP1,N 1234567.84678,E 1234567.82060,EL45.212,--

    """

    def get_point_id(self) -> str:  # noqa: D102
        return self.fields["OP"]


class SPRecord(RW5Record):
    """Occupy point record.

    Stubbed incase special handling needed in future.

    Example:
        SP,PNTEMP1,N 1324567.8468,E 1234567.8206,EL45.2120,--

    """

    def get_point_id(self) -> str:  # noqa: D102
        return self.fields["PN"]


class LSRecord(RW5Record):
    """LS record, which sets rod and instrument height. Depending on what is present in record, may indicate a change in instrument type.

    Example:
        LS,HI0.0000,HR1.4550

    """

    def update_machine_state(self):  # noqa: D102
        super().update_machine_state()
        # if we have HI & HR in the record, it indicates a switch to total station shots and we can trust
        # these values as out instrument and rod heights.
        # if we only have HR, it indicates a switch to GPS, and we should not use the HR as rod height.
        if "HI" in self.fields and "HR" in self.fields:
            self.machine_state.instrument_height = float(self.fields["HI"])
            self.machine_state.rod_height = float(self.fields["HR"])


class GPSRecord(DatedRecord):
    """GPS Record."""

    HRMS_LINE_START = "--HRMS Avg:"
    VRMS_LINE_START = "--VRMS Avg:"
    NUM_SATELLITES_LINE_START = "--Number of Satellites Avg:"
    AGE_LINE_START = "--AGE Avg:"
    HDOP_LINE_START = "--HDOP Avg:"
    VDOP_LINE_START = "--VDOP Avg:"
    PDOP_LINE_START = "--PDOP Avg:"

    def get_point_id(self) -> str:  # noqa: D102
        return self.fields["PN"]

    def _get_quality_summary_line(self) -> str | None:
        return next((line for line in self.comments if line.strip().startswith("--HRMS:")), None)

    def _get_quality_summary_line_fields(self, line: str) -> dict[str, str]:
        return {
            param.split(":")[0]: param.split(":")[1].strip() for param in line.strip().removeprefix("--").split(", ")
        }

    def _quality_fields_fallback(self) -> dict[str, str]:
        fields: dict[str, Any] = {}
        for line in self.comments:
            if line.startswith(self.HRMS_LINE_START):
                fields["HRMS"] = line[len(self.HRMS_LINE_START) :].strip().split(" ")[0]
            if line.startswith(self.VRMS_LINE_START):
                fields["VRMS"] = line[len(self.VRMS_LINE_START) :].strip().split(" ")[0]
            if line.startswith(self.HDOP_LINE_START):
                fields["HDOP"] = line[len(self.HDOP_LINE_START) :].strip().split(" ")[0]
            if line.startswith(self.VDOP_LINE_START):
                fields["VDOP"] = line[len(self.VDOP_LINE_START) :].strip().split(" ")[0]
            if line.startswith(self.PDOP_LINE_START):
                fields["PDOP"] = line[len(self.PDOP_LINE_START) :].strip().split(" ")[0]
            if line.startswith(self.AGE_LINE_START):
                fields["AGE"] = line[len(self.AGE_LINE_START) :].strip().split(" ")[0]
            if line.startswith(self.NUM_SATELLITES_LINE_START):
                fields["SATS"] = line[len(self.NUM_SATELLITES_LINE_START) :].strip().split(" ")[0]
        return fields

    def get_fields(self):
        """Parse additional GPS fields."""
        fields = super().get_fields()
        quality_summary = self._get_quality_summary_line()
        if quality_summary:
            fields.update(self._get_quality_summary_line_fields(quality_summary))
        else:
            fields.update(self._quality_fields_fallback())
        if "HRMS" not in fields:
            raise MalformedGPSRecordError
        return fields

    @property
    def hrms(self):
        value = self.fields.get("HRMS")
        return float(value) if value else None

    @property
    def vrms(self):
        value = self.fields.get("VRMS")
        return float(value) if value else None

    @property
    def hdop(self):
        value = self.fields.get("HDOP")
        return float(value) if value else None

    @property
    def vdop(self):
        value = self.fields.get("VDOP")
        return float(value) if value else None

    @property
    def pdop(self):
        value = self.fields.get("PDOP")
        return float(value) if value else None

    @property
    def tdop(self):
        value = self.fields.get("TDOP")
        return float(value) if value else None

    @property
    def gdop(self):
        value = self.fields.get("GDOP")
        return float(value) if value else None

    @property
    def age(self):
        return self.fields.get("AGE")

    @property
    def num_sats(self):
        return self.fields.get("SATS")

    @property
    def status(self):
        return self.fields.get("STATUS")


class SSRecord(DatedRecord):
    """Side shot record.

    Example:
        SS,OPTS1,FP5012,AR136.0000,ZE87.0000,SD65.000000,--CP/CP1
        --DT07-16-2025
        --TM11:57:54

    """

    def get_point_id(self) -> str:  # noqa: D102
        return self.fields["FP"]

    def get_offset_fields(self) -> dict[str, str]:
        """Check SS command block for comment record detailing a directional offset."""
        fields: dict[str, Any] = {}
        for line in self.comments:
            if line.startswith(("--Out Offset", "--In Offset", "--Right Offset", "--Left Offset")):
                fields["offset_distance"] = line.split(" Offset ")[-1].split(" ")[0]
                fields["offset_direction"] = line.removeprefix("--").split(" ")[0]
                break
        return fields

    def get_fields(self) -> dict[str, str]:  # noqa: D102
        fields = super().get_fields()
        fields.update(self.get_offset_fields())
        return fields

    @property
    def foresight_distance(self):  # noqa: D102
        return self.fields["SD"]  # slope distance a.k.a foresight distance

    @property
    def offset_distance(self) -> float | None:
        value = self.fields.get("offset_distance")
        return float(value) if value else None

    @property
    def offset_direction(self) -> str | None:
        return self.fields.get("offset_direction")


RECORD_CLASSES: dict[str, type[RW5Record]] = {
    "JB": JBRecord,
    "GPS": GPSRecord,
    "LS": LSRecord,
    "SS": SSRecord,
    "BP": BPRecord,
    "OC": OCRecord,
    "SP": SPRecord,
    "BK": BKRecord,
}
