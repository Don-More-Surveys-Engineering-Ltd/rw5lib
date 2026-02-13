import datetime
from pathlib import Path
from typing import Any

import pytest

from rw5lib.record import MachineState
from rw5lib.rw5lib import RW5Parser

rw5_encoding = "iso-8859-1"
test_rw5_files__convert: list[dict[str, Any]] = [
    {
        "rw5": Path("./tests/data/ss.test.rw5"),
        "crdb": Path("./tests/data/ss.test.crdb"),
        "num_overwritten": 1,
        "num_gps_records": 10,
        "num_bp_records": 1,
        "num_ss_records": 3,
        "num_oc_records": 1,
        "num_command_blocks": 23,
        "num_backsights": 1,
    },
    {
        "rw5": Path("./tests/data/gps-short-stats.test.rw5"),
        "crdb": None,
        "num_overwritten": 0,
        "num_gps_records": 24,
        "num_bp_records": 1,
        "num_ss_records": 0,
        "num_oc_records": 0,
        "num_command_blocks": 28,
        "num_backsights": 0,
    },
    {
        "rw5": Path("./tests/data/gps-long-stats_overwritten-shots.test.rw5"),
        "crdb": None,
        "num_overwritten": 4,
        "num_gps_records": 27,
        "num_bp_records": 1,
        "num_ss_records": 0,
        "num_oc_records": 0,
        "num_command_blocks": 42,
        "num_backsights": 0,
    },
    {
        "rw5": Path("./tests/data/gps-multiple-bp.test.rw5"),
        "crdb": None,
        "num_overwritten": 0,
        "num_gps_records": 11,
        "num_bp_records": 2,
        "num_ss_records": 0,
        "num_oc_records": 0,
        "num_command_blocks": 18,
        "num_backsights": 0,
    },
]
"""Path, GPS record count, SS record count, BP record count."""


@pytest.mark.parametrize(
    "data",
    test_rw5_files__convert,
)
def test_convert(
    data: Any,
) -> None:
    """Test that each file produces the expected number of rows per record type."""
    parser = RW5Parser(rw5_path=data["rw5"], crdb_path=None, tzinfo=None)
    result = parser.result

    csv_gps_records = [row for row in result.records if row.type == "GPS"]
    csv_bp_records = [row for row in result.records if row.type == "BP"]
    csv_ss_records = [row for row in result.records if row.type == "SS"]
    csv_oc_records = [row for row in result.records if row.type == "OC"]
    csv_bk_records = [row for row in result.records if row.type == "BK"]

    assert len(csv_gps_records) == data["num_gps_records"]
    assert len(csv_bp_records) == data["num_bp_records"]
    assert len(csv_ss_records) == data["num_ss_records"]
    assert len(csv_oc_records) == data["num_oc_records"]
    assert len(csv_bk_records) == data["num_backsights"]

    lines = data["rw5"].read_text(encoding=rw5_encoding).splitlines()

    command_blocks = RW5Parser._group_lines_into_record_blocks(lines)  # type: ignore
    assert len(command_blocks) == data["num_command_blocks"]


def test_summary_properties():
    rw5 = Path("./tests/data/ss.test.rw5")
    NUM_EQUIPMENT_EXPECTED = 2
    NUM_RTK_EXPECTED = 2
    NUM_ANTENNA_EXPECTED = 1
    JOB_NAME_EXPECTED = "19194AT240822"
    DATETIME_EXPECTED = datetime.datetime(
        year=2024, month=8, day=22, hour=15, minute=20, second=45, tzinfo=datetime.timezone.utc
    )
    result = RW5Parser(rw5_path=rw5, crdb_path=None, tzinfo=None).result
    assert len(result.equipment_summary.splitlines()) == NUM_EQUIPMENT_EXPECTED
    assert len(result.rtk_method_summary.splitlines()) == NUM_RTK_EXPECTED
    assert len(result.antenna_type_summary.splitlines()) == NUM_ANTENNA_EXPECTED
    # test job fields
    # NM19194AT240822,DT08-22-2024,TM15:20:45
    assert result.job_name == JOB_NAME_EXPECTED
    assert result.job_datetime == DATETIME_EXPECTED


def test_get_point():
    rw5 = Path("./tests/data/ss.test.rw5")
    result = RW5Parser(rw5_path=rw5, crdb_path=None, tzinfo=None).result
    # test gfetting first and last points in file
    assert result.get_point("G1").point_id == "G1"  # type: ignore
    assert result.get_point("7007").point_id == "7007"  # type: ignore


MO_RECORD = r"""MO,AD0,UN1,SF1.00000000,EC0,EO0.0,AU0
--SurvPC Version 6.08
--CRD: Alphanumeric
--User Defined: CANADA/NAD83/New Brunswick
--Equipment: Carlson,  BRx7, SN:D2133624904116, FW:6.0Aa02a,1.18,0.53.210623
--Antenna Type: [BRX7 Internal],RA0.0785m,SHMP0.0547m,L10.0701m,L20.0629m,--L1/L2/L5 Internal Antenna
--Localization File: None
--Geoid Separation File: C:\Carlson Projects\Data\Geoids\Canadian_cgg2013.gsb
--Grid Adjustment File: None
--GPS Scale: 1.00000000
--Scale Point not used
--RTK Method: RTCM V3.0, Device: Data Collector Internet, Network: NTRIP caneastvrsrtcm"""

GPS_SWITCH_TO_TOTAL_STATION = """GPS,PN6024,LA45.00000000000,LN-66.000000000000,EL23.927043,--CP/CP6
--GS,PN6024,N 1234567.8859,E 1234567.0419,EL43.3433,--CP/CP6
--GT,PN6024,SW2277,ST385749000,EW2277,ET385758000
--Valid Readings: 10 of 10
--Fixed Readings: 10 of 10
--Nor Min: 1234567.8823  Max: 1234567.8896
--Eas Min: 1234567.0372  Max: 1234567.0456
--Elv Min: 43.3382  Max: 43.3464
--Nor Avg: 1234567.8859  SD: 0.0021
--Eas Avg: 1234567.0419  SD: 0.0026
--Elv Avg: 43.3433  SD: 0.0025
--HRMS Avg: 0.0054 SD: 0.0005 Min: 0.0050 Max: 0.0067
--VRMS Avg: 0.0062 SD: 0.0006 Min: 0.0058 Max: 0.0077
--HDOP Avg: 0.5357  Min: 0.5356 Max: 0.5357
--VDOP Avg: 0.7815 Min: 0.7815 Max: 0.7817
--PDOP Avg: 0.9475 Min: 0.9474 Max: 0.9476
--AGE Avg: 1.1000 Min: 1.0000 Max: 2.0000
--Number of Satellites Avg: 15 Min: 15 Max: 15
--DT08-31-2023
--TM08:09:20
--Equipment:   Geomax Robotic,  Zoom90, SN:954977, FW:72
--TS Scale: 1.00000000
--Scale Point not used
--EDM Mode: Standard
--P.C. mm Applied: -11.3000 (Leica 360:foresight)"""

ENTERED_ROVER_HR = """BP,PN907_BASE_1,LA45.00000000000,LN-66.000000000000,EL27.7029,AG1.1880,PA0.0701,ATAPC,SRROVER,--
--Entered Rover HR: 2.0000 m, Vertical
LS,HR2.0701"""


def test_find_machine_state_changes_equipment():
    """Test parsing of equipment changes.

    First parse a MO record that has comments describing a GPS RTK system, then parse a record that has comments for a transition to totals station.
    """
    m = MachineState(equipment="A", antenna_type="A", rtk_method="A")
    RW5Parser._find_machine_state_changes(m, MO_RECORD.splitlines())  # type: ignore
    assert m.equipment and m.equipment.startswith("Carlson,  BRx7")
    assert m.antenna_type is not None
    assert m.rtk_method is not None
    RW5Parser._find_machine_state_changes(m, GPS_SWITCH_TO_TOTAL_STATION.splitlines())  # type: ignore
    assert m.equipment.startswith("Geomax Robotic")
    # should clear antenna and rtk if not found
    assert m.antenna_type is None
    assert m.rtk_method is None


def test_find_machine_state_changes_rtk():
    m = MachineState(equipment="A", antenna_type="A", rtk_method="A")
    RW5Parser._find_machine_state_changes(m, MO_RECORD.splitlines())  # type: ignore
    assert m.rtk_method and m.rtk_method.startswith("RTCM V3.0")


def test_find_machine_state_changes_antenna():
    m = MachineState(equipment="A", antenna_type="A", rtk_method="A")
    RW5Parser._find_machine_state_changes(m, MO_RECORD.splitlines())  # type: ignore
    assert m.antenna_type and m.antenna_type.startswith("[BRX7 Internal]")


def test_find_machine_state_changes_geoid():
    m = MachineState(equipment="A", antenna_type="A", rtk_method="A")
    RW5Parser._find_machine_state_changes(m, MO_RECORD.splitlines())  # type: ignore
    assert m.geoid_seperation_file and m.geoid_seperation_file.startswith(r"Canadian_cgg2013.gsb")


def test_find_machine_state_changes_projection():
    m = MachineState(equipment="A", antenna_type="A", rtk_method="A")
    RW5Parser._find_machine_state_changes(m, MO_RECORD.splitlines())  # type: ignore
    assert m.projection and m.projection == "CANADA/NAD83/New Brunswick"


def test_find_machine_state_changes_GPS_rod_height():
    m = MachineState(equipment="A", antenna_type="A", rtk_method="A")
    RW5Parser._find_machine_state_changes(m, ENTERED_ROVER_HR.splitlines())  # type: ignore
    assert m.rod_height and m.rod_height == 2


def test_find_machine_state_changes_prism():
    m = MachineState(equipment="A", antenna_type="A", rtk_method="A")
    RW5Parser._find_machine_state_changes(m, ["--P.C. mm Applied: -11.3000 (Leica 360:foresight)"])  # type: ignore
    assert m.prism_applied and m.prism_applied == "Leica 360"
    RW5Parser._find_machine_state_changes(m, ["--P.C. mm Applied: 0.0000 (Reflectorless:foresight)"])  # type: ignore
    assert m.prism_applied and m.prism_applied == "Reflectorless"
