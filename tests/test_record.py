import datetime
from typing import Any

import pytest

from rw5lib.record import RECORD_CLASSES, LSRecord, MachineState, SSRecord


@pytest.fixture
def default_machine_state():
    return MachineState()


RECORD_CHECKS: Any = [
    (
        """GPS,PN5159,LA45.00000000000,LN-66.00000000000,EL-1.648605,--TS
        --GS,PN5159,N 1234567.4778,E 1234567.9182,EL18.1924,--TS
        --GT,PN5159,SW2318,ST239822499,EW2318,ET239824500
        --Valid Readings: 3 of 3
        --Fixed Readings: 3 of 3
        --Nor Min: 1234567.4704  Max: 1234567.4852
        --Eas Min: 1234567.9131  Max: 1234567.9242
        --Elv Min: 18.1859  Max: 18.1964
        --Nor Avg: 1234567.4778  SD: 0.0060
        --Eas Avg: 1234567.9182  SD: 0.0046
        --Elv Avg: 18.1924  SD: 0.0046
        --HRMS Avg: 0.0116 SD: 0.0006 Min: 0.0109 Max: 0.0123
        --VRMS Avg: 0.0226 SD: 0.0008 Min: 0.0220 Max: 0.0238
        --HDOP Avg: 0.5661  Min: 0.5596 Max: 0.5793
        --VDOP Avg: 0.7742 Min: 0.7673 Max: 0.7878
        --PDOP Avg: 0.9591 Min: 0.9497 Max: 0.9778
        --AGE Avg: 1.3333 Min: 1.0000 Max: 2.0000
        --Number of Satellites Avg: 25 Min: 23 Max: 27
        --HRMS:0.011, VRMS:0.022, STATUS:FIXED, SATS:27, AGE:1.0, PDOP:0.950, HDOP:0.560, VDOP:0.767, TDOP:0.550, GDOP:1.098
        """,
        {
            "type": "GPS",
            "point_id": "5159",
            "fields": {
                "--": "TS",
                "STATUS": "FIXED",
                "AGE": "1.0",
                "SATS": "27",
                "HRMS": "0.011",
                "VRMS": "0.022",
                "HDOP": "0.560",
                "VDOP": "0.767",
                "PDOP": "0.950",
                "TDOP": "0.550",
                "GDOP": "1.098",
            },
        },
    ),
    (
        """GPS,PN5132,LA45.00000000000,LN-65.00000000000,EL80.214503,--UP/NEW
        --GS,PN5132,N 1234567.4786,E 1234567.3414,EL-7.9573,--UP/NEW
        --GT,PN5132,SW2334,ST134156400,EW2334,ET134159400
        --Valid Readings: XY: 3 Z: 3
        --Nor Min: 1234567.4691  Max: 1234567.4848
        --Eas Min: 1234567.3363  Max: 1234567.3487
        --Elv Min: -7.9769  Max: -7.9190
        --Nor Avg: 1234567.4786  SD: 0.0068
        --Eas Avg: 1234567.3414  SD: 0.0053
        --Elv Avg: -7.9573  SD: 0.0271
        --HRMS Avg: 0.0120 SD: 0.0023 Min: 0.0087 Max: 0.0136
        --VRMS Avg: 0.0144 SD: 0.0022 Min: 0.0113 Max: 0.0160
        --HDOP Avg: 0.5398  Min: 0.5390 Max: 0.5412
        --VDOP Avg: 0.7168 Min: 0.7157 Max: 0.7190
        --PDOP Avg: 0.8973 Min: 0.8960 Max: 0.8999
        --AGE Avg: 1.0000 Min: 1.0000 Max: 1.0000
        --Number of Satellites Avg: 22 Min: 22 Max: 23
        --Pole Incline Min: 16.2485 Max: 17.0817 Average: 16.7516
        --Incline adjustments disabled
        --HRMS:0.014, VRMS:0.016, STATUS:FIXED+, SATS:23, AGE:1.0, PDOP:0.900, HDOP:0.541, VDOP:0.719, TDOP:0.469, GDOP:1.015
        """,
        {
            "type": "GPS",
            "point_id": "5132",
            "fields": {
                "--": "UP/NEW",
                "STATUS": "FIXED+",
                "AGE": "1.0",
                "SATS": "23",
                "HRMS": "0.014",
                "VRMS": "0.016",
                "HDOP": "0.541",
                "VDOP": "0.719",
                "PDOP": "0.900",
                "TDOP": "0.469",
                "GDOP": "1.015",
            },
        },
    ),
    (
        """GPS,PN5100,LA45.00000000000,LN-65.00000000000,EL88.171642,--MON/1380HPN LOC RTK
        --GS,PN5100,N 1234567.1276,E 1234567.7300,EL0.0065,--MON/1380HPN LOC RTK
        --GT,PN5100,SW2334,ST127922600,EW2334,ET127932600
        --Valid Readings: XY: 10 Z: 10
        --Nor Min: 1234567.1264  Max: 1234567.1292
        --Eas Min: 1234567.7287  Max: 1234567.7321
        --Elv Min: 0.0030  Max: 0.0107
        --Nor Avg: 1234567.1276  SD: 0.0009
        --Eas Avg: 1234567.7300  SD: 0.0010
        --Elv Avg: 0.0065  SD: 0.0024
        --HRMS Avg: 0.0057 SD: 0.0004 Min: 0.0050 Max: 0.0062
        --VRMS Avg: 0.0092 SD: 0.0006 Min: 0.0083 Max: 0.0099
        --HDOP Avg: 0.5302  Min: 0.5302 Max: 0.5302
        --VDOP Avg: 0.6754 Min: 0.6754 Max: 0.6755
        --PDOP Avg: 0.8586 Min: 0.8586 Max: 0.8587
        --AGE Avg: 1.3000 Min: 1.0000 Max: 2.0000
        --Number of Satellites Avg: 29 Min: 29 Max: 29
        --Pole Incline Min: 0.3659 Max: 0.4026 Average: 0.3830
        --Incline adjustments disabled
        """,
        {
            "type": "GPS",
            "point_id": "5100",
            "fields": {
                "--": "MON/1380HPN LOC RTK",
                "AGE": "1.3000",
                "SATS": "29",
                "HRMS": "0.0057",
                "VRMS": "0.0092",
                "HDOP": "0.5302",
                "VDOP": "0.6754",
                "PDOP": "0.8586",
            },
        },
    ),
    (
        """GPS,PN5065,LA45.000000000000,LN-65.000000000000,EL1.877310,--TS
        --GS,PN5065,N 1234567.3886,E 1234567.0126,EL19.1685,--TS
        G0,2025/10/29 19:06:15,(Average) - Base ID read at rover: 0
        G2,VX0.00008743,VY0.00011226,VZ0.00016844
        G3,XY-0.00004820,XZ0.00002185,YZ-0.00006804
        --GT,PN5065,SW2390,ST327993600,EW2390,ET327998800
        --Valid Readings: XY: 4 Z: 4
        --Nor Min: 1234567.3779  Max: 1234567.3993
        --Eas Min: 2574245.9899  Max: 1234567.0255
        --Elv Min: 19.1586  Max: 19.1764
        --Nor Avg: 1234567.3886  SD: 0.0090
        --Eas Avg: 1234567.0126  SD: 0.0144
        --Elv Avg: 19.1685  SD: 0.0067
        --HRMS Avg: 0.0116 SD: 0.0026 Min: 0.0076 Max: 0.0147
        --VRMS Avg: 0.0147 SD: 0.0032 Min: 0.0101 Max: 0.0193
        --HDOP Avg: 0.5356  Min: 0.5337 Max: 0.5412
        --VDOP Avg: 0.7951 Min: 0.7877 Max: 0.8170
        --PDOP Avg: 0.9586 Min: 0.9515 Max: 0.9800
        --AGE Avg: 2.0000 Min: 2.0000 Max: 2.0000
        --Number of Satellites Avg: 25 Min: 25 Max: 25
        --HRMS:0.012, VRMS:0.014, STATUS:FIXED, SATS:25, AGE:2.0, PDOP:0.952, HDOP:0.534, VDOP:0.788, TDOP:0.511, GDOP:1.080
        --DT10-29-2025
        --TM16:06:30""",
        {
            "type": "GPS",
            "point_id": "5065",
            "fields": {
                "AGE": "2.0",
                "SATS": "25",
                "HRMS": "0.012",
                "VRMS": "0.014",
                "HDOP": "0.534",
                "VDOP": "0.788",
                "PDOP": "0.952",
            },
        },
    ),
    (
        """BP,PN2291_BASE_1,LA45.00000000000,LN-65.00000000000,EL7.3050,AG1.8500,PA0.0701,ATAPC,SRROVER,--
        --Entered Rover HR: 1.9900 m, Vertical
        """,
        {
            "type": "BP",
            "point_id": None,
            "fields": {"PN": "2291_BASE_1"},
        },
    ),
    (
        """LS,HI1.0000,HR0.0000""",
        {
            "type": "LS",
            "point_id": None,
            "fields": {
                "HI": "1.0000",
                "HR": "0.0000",
            },
        },
    ),
    (
        """OC,OP1,N 123.00000,E 123.00000,EL123.000,--""",
        {
            "type": "OC",
            "point_id": "1",
            "fields": {
                "--": "",
            },
        },
    ),
    (
        """BK,OP1,BPG1,BS18.5823,BC0.0000""",
        {
            "type": "BK",
            "point_id": None,
            "fields": {
                "OP": "1",
                "BP": "G1",
            },
        },
    ),
    (
        """SS,OP1,FP2,AR12.0000,ZE87.0000,SD3.000000,--
        --DT08-22-2024
        --TM16:10:29""",
        {
            "type": "SS",
            "point_id": "2",
            "fields": {
                "OP": "1",
                "SD": "3.000000",
            },
        },
    ),
    (
        """SP,PNTEMP1,N 1234567.8468,E 1234567.8206,EL45.2120,--""",
        {
            "type": "SP",
            "point_id": "TEMP1",
            "fields": {
                "N ": "1234567.8468",
                "E ": "1234567.8206",
                "EL": "45.2120",
                "--": "",
            },
        },
    ),
    (
        """SS,OP6000,FP5254,AR13.0000,ZE87.0000,SD44.000000,--BLDS B
        --Measured Offset: AR13.0000,ZE87.0000,SD44.0000
        --Left Offset 0.0500 (Relative Point Facing Instrument)
        --DT07-21-2021
        --TM08:56:18""",
        {
            "type": "SS",
            "point_id": "5254",
            "fields": {
                "offset_distance": "0.0500",
                "offset_direction": "Left",
                "--": "BLDS B",
            },
        },
    ),
]


@pytest.mark.parametrize("record_str,data", RECORD_CHECKS)
def test_parse_records(record_str: str, data: dict[str, Any], default_machine_state: MachineState):
    lines = record_str.splitlines()
    code = lines[0].split(",")[0]
    record = RECORD_CLASSES[code](lines, None, default_machine_state, datetime.timezone.utc)
    assert record.type == data["type"]
    assert record.point_id == data["point_id"]
    for key, val in data["fields"].items():
        assert record.fields[key] == val


def test_parse_ls_record_with_hr(default_machine_state: MachineState):
    """Test that the LS record changes the machine state."""
    # HR type LS records always come after a command with an "--entered rover HR" comment line in it.
    record: list[str] = "LS,HR1.4700".splitlines()  # type: ignore
    ls = LSRecord(record, None, default_machine_state, datetime.timezone.utc)
    assert ls.machine_state.rod_height == None


def test_parse_ls_record_with_hr_and_hi(default_machine_state: MachineState):
    """Test that the LS record changes the machine state."""
    record: list[str] = "LS,HI1.5450,HR1.4700".splitlines()  # type: ignore
    ls = LSRecord(record, None, default_machine_state, datetime.timezone.utc)
    assert ls.machine_state.instrument_height == 1.545
    assert ls.machine_state.rod_height == 1.47


def test_dated_record(default_machine_state: MachineState):
    record: list[str] = """SS,OP6000,FP5254,AR13.5305,ZE87.5336,SD44.879765,--BLDS B
    --Measured Offset: AR13.4916,ZE87.5336,SD44.8797
    --Left Offset 0.0500 (Relative Point Facing Instrument)
    --DT07-21-2021
    --TM08:56:18""".splitlines()  # type: ignore
    DATETIME_EXPECTED = datetime.datetime(
        year=2021, month=7, day=21, hour=8, minute=56, second=18, tzinfo=datetime.timezone.utc
    )
    ss = SSRecord(record, None, default_machine_state, datetime.timezone.utc)
    assert ss.datetime == DATETIME_EXPECTED
