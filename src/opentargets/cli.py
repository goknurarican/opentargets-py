"""Typer-based CLI for the Open Targets Platform SDK.

Usage examples::

    opentargets target EGFR
    opentargets target EGFR --json
    opentargets target EGFR --associations --drugs
    opentargets targets EGFR BRAF KRAS --json
    opentargets disease EFO_0000311
    opentargets disease EFO_0000311 --targets --json
    opentargets drug CHEMBL941
    opentargets drug CHEMBL941 --indications --json
    opentargets search "lung cancer" --json
    opentargets associations EGFR --limit 10 --json
"""

from __future__ import annotations

import json
from typing import Any, Optional

import typer
from rich.console import Console
from rich.table import Table

from .client import OpenTargetsClient
from .exceptions import APIError, NotFoundError, QueryError

app = typer.Typer(
    name="opentargets",
    help="Query the Open Targets Platform from the command line.",
    add_completion=False,
    no_args_is_help=True,
)

_err_console = Console(stderr=True)


def _err(msg: str) -> None:
    _err_console.print(f"[bold red]Error:[/bold red] {msg}")


def _json_out(data: object) -> None:
    typer.echo(json.dumps(data, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# target
# ---------------------------------------------------------------------------


@app.command()
def target(
    target_id: str = typer.Argument(
        ..., help="Ensembl ID or gene symbol (e.g. EGFR)"
    ),
    associations: bool = typer.Option(
        False, "--associations", help="Include top associations"
    ),
    drugs: bool = typer.Option(False, "--drugs", help="Include known drugs"),
    tractability: bool = typer.Option(
        False, "--tractability", help="Include tractability data"
    ),
    safety: bool = typer.Option(
        False, "--safety", help="Include safety liabilities"
    ),
    expression: bool = typer.Option(
        False, "--expression", help="Include tissue expression"
    ),
    constraint: bool = typer.Option(
        False, "--constraint", help="Include genetic constraint"
    ),
    limit: int = typer.Option(10, "--limit", help="Max associations/drugs to show"),
    json_out: bool = typer.Option(False, "--json", help="Output raw JSON"),
    debug: bool = typer.Option(False, "--debug", help="Show full tracebacks on error"),
) -> None:
    """Look up a single target."""
    client = OpenTargetsClient()
    try:
        t = client.get_target(target_id)
        result: dict[str, Any] = t.model_dump(mode="json")

        if associations:
            assocs = client.get_target_associations(target_id, limit=limit)
            result["associations"] = [
                a.model_dump(mode="json") for a in assocs
            ]

        if drugs:
            drug_list = client.get_target_drugs(target_id)
            result["drugs"] = [d.model_dump(mode="json") for d in drug_list]

        if tractability:
            tract = client.get_target_tractability(target_id)
            result["tractability"] = [tr.model_dump(mode="json") for tr in tract]

        if safety:
            safety_data = client.get_target_safety(target_id)
            result["safety"] = [s.model_dump(mode="json") for s in safety_data]

        if expression:
            expr = client.get_target_expression(target_id)
            result["expression"] = [e.model_dump(mode="json") for e in expr]

        if constraint:
            constr = client.get_target_constraint(target_id)
            result["constraint"] = [c.model_dump(mode="json") for c in constr]

    except (NotFoundError, APIError, QueryError) as exc:
        if debug:
            raise
        _err(str(exc))
        raise typer.Exit(code=1) from exc

    if json_out:
        _json_out(result)
        return

    console = Console()
    sym = result.get("approved_symbol", target_id)
    tbl = Table(title=f"Target: {sym}", show_header=True)
    tbl.add_column("Field", style="bold cyan")
    tbl.add_column("Value")
    tbl.add_row("ID", result.get("id", ""))
    tbl.add_row("Symbol", result.get("approved_symbol", ""))
    tbl.add_row("Name", result.get("approved_name", ""))
    tbl.add_row("Biotype", result.get("biotype", ""))
    desc = result.get("description", "")
    if desc:
        tbl.add_row("Description", desc[:120] + ("…" if len(desc) > 120 else ""))
    console.print(tbl)

    if "associations" in result:
        a_tbl = Table(title="Top Associations", show_header=True)
        a_tbl.add_column("Disease", style="cyan")
        a_tbl.add_column("Disease ID")
        a_tbl.add_column("Score", justify="right")
        for a in result["associations"]:
            a_tbl.add_row(a["disease_name"], a["disease_id"], f"{a['score']:.3f}")
        console.print(a_tbl)

    if "drugs" in result:
        d_tbl = Table(title="Known Drugs", show_header=True)
        d_tbl.add_column("ID", style="cyan")
        d_tbl.add_column("Name")
        d_tbl.add_column("Type")
        d_tbl.add_column("Phase")
        for d in result["drugs"]:
            phase = str(d.get("max_clinical_trial_phase") or "")
            d_tbl.add_row(d["id"], d["name"], d["drug_type"], phase)
        console.print(d_tbl)

    if "tractability" in result:
        tr_tbl = Table(title="Tractability", show_header=True)
        tr_tbl.add_column("Modality")
        tr_tbl.add_column("Label")
        tr_tbl.add_column("Value")
        for tr in result["tractability"]:
            tr_tbl.add_row(tr["modality"], tr["label"], str(tr["value"]))
        console.print(tr_tbl)

    if "constraint" in result:
        c_tbl = Table(title="Genetic Constraint", show_header=True)
        c_tbl.add_column("Type")
        c_tbl.add_column("OE")
        c_tbl.add_column("Score")
        for c in result["constraint"]:
            oe = f"{c['oe']:.3f}" if c.get("oe") is not None else ""
            score = f"{c['score']:.3f}" if c.get("score") is not None else ""
            c_tbl.add_row(c.get("constraint_type", ""), oe, score)
        console.print(c_tbl)

    console.print("[dim]Tip: use --json for full machine-readable output[/dim]")


# ---------------------------------------------------------------------------
# targets
# ---------------------------------------------------------------------------


@app.command()
def targets(
    target_ids: list[str] = typer.Argument(  # noqa: B008
        ..., help="One or more Ensembl IDs or gene symbols"
    ),
    json_out: bool = typer.Option(False, "--json", help="Output raw JSON"),
    debug: bool = typer.Option(False, "--debug", help="Show full tracebacks on error"),
) -> None:
    """Look up multiple targets in a single request."""
    client = OpenTargetsClient()
    try:
        results = client.get_targets(target_ids)
    except (NotFoundError, APIError, QueryError) as exc:
        if debug:
            raise
        _err(str(exc))
        raise typer.Exit(code=1) from exc

    data = [t.model_dump(mode="json") for t in results]

    if json_out:
        _json_out(data)
        return

    console = Console()
    tbl = Table(title="Targets", show_header=True)
    tbl.add_column("ID", style="cyan")
    tbl.add_column("Symbol", style="bold")
    tbl.add_column("Name")
    tbl.add_column("Biotype")
    for t in data:
        tbl.add_row(t["id"], t["approved_symbol"], t["approved_name"], t["biotype"])
    console.print(tbl)
    console.print("[dim]Tip: use --json for full machine-readable output[/dim]")


# ---------------------------------------------------------------------------
# disease
# ---------------------------------------------------------------------------


@app.command()
def disease(
    disease_id: str = typer.Argument(
        ..., help="EFO identifier (e.g. EFO_0000311)"
    ),
    show_targets: bool = typer.Option(
        False, "--targets", help="Include associated targets"
    ),
    limit: int = typer.Option(10, "--limit", help="Max associated targets to show"),
    json_out: bool = typer.Option(False, "--json", help="Output raw JSON"),
    debug: bool = typer.Option(False, "--debug", help="Show full tracebacks on error"),
) -> None:
    """Look up a disease by EFO identifier."""
    client = OpenTargetsClient()
    try:
        d = client.get_disease(disease_id)
        result: dict[str, Any] = d.model_dump(mode="json")

        if show_targets:
            assocs = client.get_disease_targets(disease_id, limit=limit)
            result["targets"] = [
                a.model_dump(mode="json") for a in assocs
            ]

    except (NotFoundError, APIError, QueryError) as exc:
        if debug:
            raise
        _err(str(exc))
        raise typer.Exit(code=1) from exc

    if json_out:
        _json_out(result)
        return

    console = Console()
    name = result.get("name", disease_id)
    tbl = Table(title=f"Disease: {name}", show_header=True)
    tbl.add_column("Field", style="bold cyan")
    tbl.add_column("Value")
    tbl.add_row("ID", result.get("id", ""))
    tbl.add_row("Name", result.get("name", ""))
    desc = result.get("description", "")
    if desc:
        tbl.add_row("Description", desc[:120] + ("…" if len(desc) > 120 else ""))
    areas = result.get("therapeutic_areas") or []
    if areas:
        tbl.add_row("Therapeutic Areas", ", ".join(areas[:5]))
    console.print(tbl)

    if "targets" in result:
        t_tbl = Table(title="Associated Targets", show_header=True)
        t_tbl.add_column("Symbol", style="cyan")
        t_tbl.add_column("Target ID")
        t_tbl.add_column("Score", justify="right")
        for a in result["targets"]:
            t_tbl.add_row(a["target_symbol"], a["target_id"], f"{a['score']:.3f}")
        console.print(t_tbl)

    console.print("[dim]Tip: use --json for full machine-readable output[/dim]")


# ---------------------------------------------------------------------------
# drug
# ---------------------------------------------------------------------------


@app.command()
def drug(
    drug_id: str = typer.Argument(
        ..., help="ChEMBL identifier (e.g. CHEMBL941)"
    ),
    indications: bool = typer.Option(
        False, "--indications", help="Include disease indications"
    ),
    chembl_ids: bool = typer.Option(
        False, "--chembl-ids", help="Include all ChEMBL cross-reference IDs"
    ),
    json_out: bool = typer.Option(False, "--json", help="Output raw JSON"),
    debug: bool = typer.Option(False, "--debug", help="Show full tracebacks on error"),
) -> None:
    """Look up a drug by ChEMBL identifier."""
    client = OpenTargetsClient()
    try:
        d = client.get_drug(drug_id)
        result: dict[str, Any] = d.model_dump(mode="json")

        if indications:
            ind_list = client.get_drug_indications(drug_id)
            result["indications"] = [i.model_dump(mode="json") for i in ind_list]

        if chembl_ids:
            result["chembl_ids"] = client.get_drug_chembl_ids(drug_id)

    except (NotFoundError, APIError, QueryError) as exc:
        if debug:
            raise
        _err(str(exc))
        raise typer.Exit(code=1) from exc

    if json_out:
        _json_out(result)
        return

    console = Console()
    tbl = Table(title=f"Drug: {result.get('name', drug_id)}", show_header=True)
    tbl.add_column("Field", style="bold cyan")
    tbl.add_column("Value")
    tbl.add_row("ID", result.get("id", ""))
    tbl.add_row("Name", result.get("name", ""))
    tbl.add_row("Type", result.get("drug_type", ""))
    tbl.add_row("Mechanism", result.get("mechanism_of_action", ""))
    tbl.add_row("Max Phase", str(result.get("max_clinical_trial_phase") or ""))
    synonyms = result.get("synonyms") or []
    if synonyms:
        tbl.add_row("Synonyms", ", ".join(synonyms[:5]))
    trade_names = result.get("trade_names") or []
    if trade_names:
        tbl.add_row("Trade Names", ", ".join(trade_names[:5]))
    console.print(tbl)

    if "indications" in result:
        i_tbl = Table(title="Indications", show_header=True)
        i_tbl.add_column("Disease", style="cyan")
        i_tbl.add_column("Disease ID")
        i_tbl.add_column("Max Phase")
        for ind in result["indications"]:
            phase = str(ind.get("max_phase_for_indication") or "")
            i_tbl.add_row(
                ind.get("disease_name", ""),
                ind.get("disease_id", ""),
                phase,
            )
        console.print(i_tbl)

    console.print("[dim]Tip: use --json for full machine-readable output[/dim]")


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


@app.command()
def search(
    query: str = typer.Argument(..., help="Free-text search query"),
    entity_type: Optional[str] = typer.Option(
        None, "--entity", help="Filter: target, disease, or drug"
    ),
    limit: int = typer.Option(10, "--limit", help="Maximum results to return"),
    json_out: bool = typer.Option(False, "--json", help="Output raw JSON"),
    debug: bool = typer.Option(False, "--debug", help="Show full tracebacks on error"),
) -> None:
    """Search the Open Targets Platform."""
    client = OpenTargetsClient()
    try:
        results = client.search(query, entity_type=entity_type, limit=limit)
    except (NotFoundError, APIError, QueryError) as exc:
        if debug:
            raise
        _err(str(exc))
        raise typer.Exit(code=1) from exc

    data = [r.model_dump(mode="json") for r in results]

    if json_out:
        _json_out(data)
        return

    console = Console()
    tbl = Table(title=f'Search: "{query}"', show_header=True)
    tbl.add_column("ID", style="cyan")
    tbl.add_column("Name", style="bold")
    tbl.add_column("Type")
    tbl.add_column("Score", justify="right")
    tbl.add_column("Description")
    for r in data:
        desc = r.get("description", "")
        tbl.add_row(
            r["id"],
            r["name"],
            r["entity_type"],
            f"{r['score']:.2f}",
            desc[:60] + ("…" if len(desc) > 60 else ""),
        )
    console.print(tbl)
    console.print("[dim]Tip: use --json for full machine-readable output[/dim]")


# ---------------------------------------------------------------------------
# associations
# ---------------------------------------------------------------------------


@app.command()
def associations(
    target_id: str = typer.Argument(..., help="Ensembl ID or gene symbol"),
    limit: int = typer.Option(10, "--limit", help="Max associations to return"),
    json_out: bool = typer.Option(False, "--json", help="Output raw JSON"),
    debug: bool = typer.Option(False, "--debug", help="Show full tracebacks on error"),
) -> None:
    """Fetch diseases associated with a target."""
    client = OpenTargetsClient()
    try:
        assocs = client.get_target_associations(target_id, limit=limit)
    except (NotFoundError, APIError, QueryError) as exc:
        if debug:
            raise
        _err(str(exc))
        raise typer.Exit(code=1) from exc

    data = [a.model_dump(mode="json") for a in assocs]

    if json_out:
        _json_out(data)
        return

    console = Console()
    tbl = Table(title=f"Associations for {target_id}", show_header=True)
    tbl.add_column("Disease", style="cyan")
    tbl.add_column("Disease ID")
    tbl.add_column("Score", justify="right")
    tbl.add_column("# Datasources", justify="right")
    for a in data:
        tbl.add_row(
            a["disease_name"],
            a["disease_id"],
            f"{a['score']:.3f}",
            str(len(a.get("datasource_scores", []))),
        )
    console.print(tbl)
    console.print("[dim]Tip: use --json for full machine-readable output[/dim]")


def main() -> None:
    """Entry point for the opentargets CLI."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
