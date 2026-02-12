from pathlib import Path

from rw5lib.rw5lib import RW5Parser
from rw5lib.totalstation import plot_total_station_data


def test_find_total_stations():
    # this set of files has a single totalstation setup
    # The OC is point 1, the BK is point G1, and the sideshots are 2, 3, and 4
    rw5 = Path("./tests/data/ss.test.rw5")
    crdb = Path("./tests/data/ss.test.crdb")
    parser = RW5Parser(rw5_path=rw5, crdb_path=crdb, tzinfo=None)
    EXPECTED_BACKSIGHT_DISTANCE = 80.697
    result = parser.result
    assert len(result.ts_stations) == 1
    station = result.ts_stations[0]
    assert station.oc.point_id == "1"
    assert station.backsight.fields["BP"] == "G1"
    assert len(station.side_shots) == 3
    assert [s.point_id for s in station.side_shots] == ["2", "3", "4"]
    assert station.backsight_distance and abs(station.backsight_distance - EXPECTED_BACKSIGHT_DISTANCE) <= 0.001


def test_plot_total_station_data_produces_bytes():
    rw5 = Path("./tests/data/ss.test.rw5")
    crdb = Path("./tests/data/ss.test.crdb")
    parser = RW5Parser(rw5_path=rw5, crdb_path=crdb, tzinfo=None)
    png_bytes = plot_total_station_data(parser.result, crdb_path=crdb)
    assert len(png_bytes.read()) > 0
