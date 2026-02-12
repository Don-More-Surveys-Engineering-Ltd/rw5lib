from functools import cached_property

from rw5lib.record import RW5Record
from rw5lib.totalstation import TSStation


class RW5Result:
    """Final result of processing an RW5 file.

    Used to aggregate data as processing happens.
    """

    records: list[RW5Record]
    ts_stations: list[TSStation]
    """Total station 'stations'."""

    @cached_property
    def equipment_summary(self):
        return ",\n".join({r.machine_state.equipment for r in self.records if r.machine_state.equipment is not None})

    @cached_property
    def antenna_type_summary(self):
        return ",\n".join(
            {r.machine_state.antenna_type for r in self.records if r.machine_state.antenna_type is not None}
        )

    @cached_property
    def rtk_method_summary(self):
        return ",\n".join({r.machine_state.rtk_method for r in self.records if r.machine_state.rtk_method is not None})

    @cached_property
    def geoid_seperation_file_summary(self):
        return ",\n".join(
            {
                r.machine_state.geoid_seperation_file
                for r in self.records
                if r.machine_state.geoid_seperation_file is not None
            }
        )

    @cached_property
    def projection_summary(self):
        return ",\n".join({r.machine_state.projection for r in self.records if r.machine_state.projection is not None})

    @cached_property
    def _job_record(self):
        return next((r for r in self.records if r.type == "JB"), None)

    @property
    def job_name(self):
        if not self._job_record:
            return None
        return self._job_record.machine_state.job

    @property
    def job_datetime(self):
        if not self._job_record:
            return None
        return self._job_record.machine_state.job_datetime

    @cached_property
    def _point_id_dict(self):
        return {r.point_id: r for r in self.records if r.point_id is not None}

    def get_point(self, point_id: str):
        return self._point_id_dict.get(point_id, None)

    def __init__(self) -> None:
        self.records = []
        self.ts_stations = []
