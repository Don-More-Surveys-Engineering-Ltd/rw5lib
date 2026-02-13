import io
import math
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt  # v 3.3.2

from rw5lib.record import BKRecord, OCRecord, RW5Record
from rw5lib.utils import get_crdb_coordinate

if TYPE_CHECKING:
    from rw5lib.result import RW5Result


@dataclass
class TSStation:
    """Dataclass describing a totalstation system."""

    oc: OCRecord
    backsight: BKRecord
    side_shots: list[RW5Record]
    backsight_angle_dd: float | None
    backsight_distance: float | None


Point2DType = tuple[float, float]
ExtentType = tuple[float, float, float, float]


def get_extent(rows: list[tuple[float, float, float]]) -> ExtentType:
    minx = math.inf
    miny = math.inf
    maxx = -math.inf
    maxy = -math.inf

    for row in rows:
        if row[0] and row[0] < minx:
            minx = float(row[0])
        if row[0] and row[0] > maxx:
            maxx = float(row[0])
        if row[1] and row[1] < miny:
            miny = float(row[1])
        if row[1] and row[1] > maxy:
            maxy = float(row[1])

    return (minx, miny, maxx, maxy)


def scale_to_new_dimensions(p: Point2DType, old_extent: ExtentType, new_extent: ExtentType) -> Point2DType:
    old_range_x = old_extent[2] - old_extent[0]
    old_range_y = old_extent[3] - old_extent[1]
    new_range_x = new_extent[2] - new_extent[0]
    new_range_y = new_extent[3] - new_extent[1]

    scale = min(
        new_range_x / (old_range_y or 1),
        new_range_y / (old_range_y or 1),
    )

    margin_x = new_range_x - old_range_x * scale
    margin_y = new_range_y - old_range_y * scale

    scaled_x = new_extent[0] + ((p[0] - old_extent[0]) * scale) + margin_x / 2
    scaled_y = new_extent[1] + ((p[1] - old_extent[1]) * scale) + margin_y / 2
    return (scaled_x, scaled_y)


def plot_total_station_data(result: "RW5Result", crdb_path: Path) -> io.BytesIO:
    """Plot ts data with matplotlib.

    Returns BytesIO object containing png data.
    """
    applicable_records = [
        r for r in result.records if r.type in {"OC", "SS", "BK", "GPS", "SP"} and r.point_id is not None
    ]
    coords: dict[str, tuple[float, float, float]] = {}
    for record in applicable_records:
        if not record.point_id:
            continue
        try:
            coords[record.point_id] = get_crdb_coordinate(record.point_id, crdb_path)
        except ValueError:
            pass
    # setup figure
    extent = get_extent(
        [coords[r.point_id] for r in applicable_records if r.point_id],
    )
    new_extent = (0, 0, 10, 10)
    fig, ax = plt.subplots(figsize=new_extent[2:], dpi=128)
    plt.axis("off")
    # create a plot for each OC record,
    # assumeing that OC records are a good tell for when a nmew system has
    #   been started.
    for station in result.ts_stations:
        # add backsight
        assert station.oc.point_id is not None
        oc_coords = coords[station.oc.point_id]
        bk_coords = coords[station.backsight.fields["BP"]]
        from_scaled = scale_to_new_dimensions(
            (float(oc_coords[0]), float(oc_coords[1])),
            extent,
            new_extent,
        )
        to_scaled = scale_to_new_dimensions((bk_coords[0], bk_coords[1]), extent, new_extent)
        ax.plot([from_scaled[0], to_scaled[0]], [from_scaled[1], to_scaled[1]], "r", linewidth=4, alpha=0.3)
        # plot bs point
        p = (bk_coords[0], bk_coords[1])
        scaled_p = scale_to_new_dimensions(p, extent, new_extent)
        ax.plot(scaled_p[0], scaled_p[1], "r^", alpha=0.7, markersize=22)
        # annotate marker with point id
        ax.annotate(
            station.backsight.fields["BP"],
            (scaled_p[0], scaled_p[1]),
            ha="left",
            va="center",
            fontsize="xx-large",
            color="black",
        )
        # add sideshot lines
        for ss in station.side_shots:
            assert ss.point_id is not None
            ss_coords = coords[ss.point_id]
            from_scaled = scale_to_new_dimensions(
                (oc_coords[0], oc_coords[1]),
                extent,
                new_extent,
            )
            to_scaled = scale_to_new_dimensions((ss_coords[0], ss_coords[1]), extent, new_extent)
            ax.plot([from_scaled[0], to_scaled[0]], [from_scaled[1], to_scaled[1]], "b", linewidth=4, alpha=0.1)
        # plot oc
        p = (oc_coords[0], oc_coords[1])
        scaled_p = scale_to_new_dimensions(p, extent, new_extent)
        ax.plot(scaled_p[0], scaled_p[1], "g^", alpha=0.7, markersize=22)
        # add label for OC
        ax.annotate(
            station.oc.point_id,
            (scaled_p[0], scaled_p[1]),
            ha="left",
            va="center",
            fontsize="xx-large",
            color="black",
        )
        # add sideshot points (on top of everything because they're smaller)
        for ss in station.side_shots:
            assert ss.point_id is not None
            ss_coords = coords[ss.point_id]
            p = (ss_coords[0], ss_coords[1])
            scaled_p = scale_to_new_dimensions(p, extent, new_extent)
            ax.plot(scaled_p[0], scaled_p[1], "bo", markersize=10)
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    return buffer
