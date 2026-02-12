"""Console script for rw5lib."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from rw5lib.result import RW5Result
from rw5lib.rw5lib import RW5Parser
from rw5lib.totalstation import plot_total_station_data

app = typer.Typer()
console = Console()


@app.command()
def print(
    rw5: Annotated[str, typer.Option("--rw5", help="Path to rw5 file.")],
    crdb: Annotated[str | None, typer.Option(help="Path to crdb file. Required for total station features.")] = None,
    type_filter: Annotated[str | None, typer.Option("--type", "-t", help="Filter points by record type.")] = None,
    fields_str: Annotated[
        str | None, typer.Option("--fields", "-f", help="Point fields to show in table (comma seperated).")
    ] = None,
    machine_state_fields_str: Annotated[
        str | None,
        typer.Option("--machine-state-fields", "-m", help="Machine state fields to show in table (comma seperated)."),
    ] = None,
):
    """Console script for rw5lib."""
    parser = RW5Parser(
        rw5_path=Path(rw5),
        crdb_path=Path(crdb) if crdb else None,
        tzinfo=None,
    )
    result = parser.result
    fields: list[str] = fields_str.split(",") if fields_str else []
    machine_state_fields: list[str] = machine_state_fields_str.split(",") if machine_state_fields_str else []
    table = Table("Record #", "Type", "Point ID", *fields, *machine_state_fields)
    for i, record in enumerate(result.records):
        if type_filter and record.type.lower() != type_filter.lower():
            continue
        field_values = [record.fields.get(f) for f in fields]
        machine_state_dict = asdict(record.machine_state)
        machine_state_field_values = [machine_state_dict.get(f) for f in machine_state_fields]
        table.add_row(str(i), record.type, record.point_id, *field_values, *machine_state_field_values)
    console.print(table)
    console.print_json(
        json.dumps(
            {
                "equipment": result.equipment_summary,
                "antenna_type": result.antenna_type_summary,
                "geoid_seperation_file": result.geoid_seperation_file_summary,
                "rtk_method": result.rtk_method_summary,
                "job_name": result.job_name,
                "job_datetime": str(result.job_datetime),
            }
        )
    )


@app.command()
def totalstations(
    rw5: Annotated[str, typer.Option("--rw5", help="Path to rw5 file.")],
    crdb: Annotated[str, typer.Option(help="Path to crdb file. Required for total station features.")],
    plot: Annotated[str | None, typer.Option(help="Output path to save plotted image to.")] = None,
):
    """Console script for rw5lib."""
    parser = RW5Parser(
        rw5_path=Path(rw5),
        crdb_path=Path(crdb),
        tzinfo=None,
    )
    result = parser.result
    table = Table(
        "Station #",
        "Occupied",
        "Backsight",
        "Sideshots",
    )
    for i, ts in enumerate(result.ts_stations):
        table.add_row(
            str(i), ts.oc.point_id, ts.backsight.fields["BP"], ", ".join([str(s.point_id) for s in ts.side_shots])
        )
    console.print(table)
    if plot:
        Path(plot).write_bytes(plot_total_station_data(result, Path(crdb)).read())


@app.command()
def points(
    points: Annotated[str, typer.Argument(help="Comma seperated point ids or point id ranges.")],
    rw5: Annotated[str, typer.Option(help="Path to rw5 file.")],
    crdb: Annotated[str | None, typer.Option(help="Path to crdb file. Required for total station features.")] = None,
):
    """Console script for rw5lib."""
    parser = RW5Parser(
        rw5_path=Path(rw5),
        crdb_path=Path(crdb) if crdb else None,
        tzinfo=None,
    )
    result = parser.result
    for point_range in points.split(","):
        if "-" not in point_range:
            print_point_summary(result, point_range)
        else:
            start, end = point_range.split("-")[:2]
            for i in range(int(start), int(end) + 1):
                print_point_summary(result, str(i))


def print_point_summary(result: RW5Result, point_id: str):
    point = result.get_point(point_id)
    if point is None:
        console.print(f"[bold red]No such point {point_id}.[/bold red]")
        raise typer.Exit()
    console.print(f"[bold blue]{point_id}:[/bold blue]")
    table = Table("Key", "Value")
    for key, val in point.fields.items():
        table.add_row(key, str(val))
    table.add_section()
    for key, val in asdict(point.machine_state).items():
        if val is not None:
            table.add_row(f"MachineState.{key}", str(val))
    console.print(table)


if __name__ == "__main__":
    app()
