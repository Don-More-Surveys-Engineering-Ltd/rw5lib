"""Main module."""

import copy
import datetime
import logging
import math
from pathlib import Path

from rw5lib.exceptions import MalformedGPSRecordError
from rw5lib.record import RECORD_CLASSES, BKRecord, MachineState, OCRecord
from rw5lib.result import RW5Result
from rw5lib.totalstation import TSStation
from rw5lib.utils import dms_to_dd, get_crdb_coordinate

logger = logging.getLogger(__name__)


class RW5Parser:
    machine_state: MachineState
    rw5_path: Path
    crdb_path: Path | None
    tzinfo: datetime.tzinfo
    result: RW5Result

    def __init__(self, *, rw5_path: Path, crdb_path: Path | None, tzinfo: datetime.tzinfo | None) -> None:
        self.rw5_path = rw5_path
        self.crdb_path = crdb_path
        self.tzinfo = tzinfo or datetime.timezone.utc
        self.machine_state = MachineState()
        self.result = RW5Result()
        self._parse()

    def _parse(self) -> None:
        visited_point_ids: set[str] = set()
        # group file into record blocks
        with self.rw5_path.open("r", encoding="iso8859-1") as input_file:
            record_blocks = self._group_lines_into_record_blocks(input_file.readlines())
        for index, block in enumerate(record_blocks):
            record_code = block[0].split(",")[0].strip()
            if record_code in RECORD_CLASSES:
                # create/parse record
                try:
                    curr_record = RECORD_CLASSES[record_code](
                        block,
                        record_blocks[index - 1] if index > 0 else None,
                        self.machine_state,
                        self.tzinfo,
                    )
                    # if point id seen already...
                    if curr_record.point_id is not None and curr_record.point_id in visited_point_ids:
                        # remove the earlier verion of the point
                        self.result.records = [r for r in self.result.records if r.point_id != curr_record.point_id]
                    # copy over potentially updated machine state
                    self.machine_state = copy.deepcopy(curr_record.machine_state)
                    # append record
                    self.result.records.append(curr_record)
                    # make note that we've visited a record with this point id before
                    if curr_record.point_id is not None:
                        visited_point_ids.add(curr_record.point_id)
                except MalformedGPSRecordError:
                    # if record is malformed, fail silently and continue
                    pass
            else:
                logger.debug(f"No record class found for record code {record_code}.")
            # post record hooks
            self._find_machine_state_changes(self.machine_state, block)  # type: ignore
        # find total stations if crdb available
        if self.crdb_path:
            self.find_total_stations()

    @staticmethod
    def _find_machine_state_changes(machine_state: MachineState, block: list[str]):
        """Check record block for changes to the machine state.

        A change found in a block does not apply to the current shot, but the following.
        Thus this should be called after a record has been parsed.
        """
        prism_prefix = "--P.C. mm Applied:"
        rover_height_prefix = "--Entered Rover HR:"
        equipment_prefix = "--Equipment:"
        antenna_prefix = "--Antenna Type:"
        rtk_prefix = "--RTK Method:"
        geoid_prefix = "--Geoid Separation File:"
        projection_prefix_1 = "--User Defined:"
        projection_prefix_2 = "--Projection:"
        for line in block:
            # === PRISM ===
            if line.startswith(prism_prefix):
                machine_state.prism_applied = line.split("(", maxsplit=1)[-1].split(":", maxsplit=1)[0]
            # === GPS-TYPE ROD HEIGHT ===
            if line.startswith(rover_height_prefix):
                machine_state.instrument_height = None
                machine_state.rod_height = float(line.removeprefix(rover_height_prefix).split()[0])
            # === EQUIPMENT ===
            if line.startswith(equipment_prefix):
                machine_state.equipment = line.removeprefix(equipment_prefix).strip()
                # change in equipment should reset antenna and rtk method
                machine_state.antenna_type = None
                machine_state.rtk_method = None
            # === ANTENNA ===
            if line.startswith(antenna_prefix):
                machine_state.antenna_type = line.removeprefix(antenna_prefix).strip()
            # === RTK ===
            if line.startswith(rtk_prefix):
                machine_state.rtk_method = line.removeprefix(rtk_prefix).strip()
            # === GEOID SEPERATION FILE ===
            if line.startswith(geoid_prefix):
                machine_state.geoid_seperation_file = line.removeprefix(geoid_prefix).split("\\")[-1].split(" ")[0]
            # === PROJECTION ===
            if line.startswith(projection_prefix_1):
                machine_state.projection = line.removeprefix(projection_prefix_1).strip()
            if line.startswith(projection_prefix_2):
                machine_state.projection = line.removeprefix(projection_prefix_2).strip()

    @staticmethod
    def _group_lines_into_record_blocks(lines: list[str]) -> list[list[str]]:
        """Group file lines into record blocks.

        Some lines start with prefixes that we want to ignore and not interrupt the record that they're within

        Example:
            GPS _____________________________   // Command starts
            --blahs blah blah
            G0 blah blah                        // Skip this line (prefix == G0)
            G1 blah blah                        // Skip this line
            G2 blah blah                        // Skip this line
            --blahs blah blah blah
            --blah                              // Command ends
            GPS ____________________________    // New command starts

        """
        skip_lines_with_prefixes = ["G0", "G1", "G2", "G3"]
        commands: list[list[str]] = []
        active_command: list[str] = []
        stripped_lines = [line.strip() for line in lines]
        for line in stripped_lines:
            # skips lines with specific prefixes, act line they're not even there.
            if any(line.startswith(prefix) for prefix in skip_lines_with_prefixes):
                continue
            line_is_comment = line.startswith("--")
            # If theres an active command and this line isn't comment
            #   Finish active command, start new command
            if len(active_command) > 0 and line_is_comment is False:
                commands.append(active_command)
                active_command = []
            # Append current line to active_command
            active_command.append(line)
        if len(active_command) > 0:
            commands.append(active_command)
        return commands

    def find_total_stations(self):
        if not self.crdb_path:
            raise ValueError
        oc_records = [r for r in self.result.records if isinstance(r, OCRecord)]
        for oc_record in oc_records:
            assert oc_record.point_id is not None
            bk_record = next(
                r for r in self.result.records if isinstance(r, BKRecord) and r.fields["OP"] == oc_record.point_id
            )
            # calculate backsight distance (haversine distance between occupied point and backsight point)
            oc_coords = get_crdb_coordinate(oc_record.point_id, self.crdb_path)
            bk_coords = get_crdb_coordinate(bk_record.fields["BP"], self.crdb_path)
            backsight_distance = math.sqrt(
                ((oc_coords[0] - bk_coords[0]) ** 2)
                + ((oc_coords[1] - bk_coords[1]) ** 2)
                + ((oc_coords[2] - bk_coords[2]) ** 2),
            )
            # calculate backsight angle in dd
            backsight_angle_dd = dms_to_dd(bk_record.fields["BS"])
            # find all side shots for station
            ss_records = [r for r in self.result.records if r.type == "SS" and r.fields["OP"] == oc_record.point_id]
            self.result.ts_stations.append(
                TSStation(
                    oc=oc_record,
                    backsight=bk_record,
                    backsight_angle_dd=backsight_angle_dd,
                    backsight_distance=backsight_distance,
                    side_shots=ss_records,
                ),
            )
