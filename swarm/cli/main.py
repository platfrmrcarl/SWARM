from __future__ import annotations
import asyncio
import sys
from pathlib import Path

import typer
import yaml

app = typer.Typer(help="SWARM — multi-agent coordination library")


def run_swarm(config_path: Path, task: str, api_key: str | None = None):
    from swarm.builder.swarm import Swarm
    from swarm.builder.config import build_provider
    from swarm.agents.llm_agent import LLMAgent

    cfg = yaml.safe_load(config_path.read_text())
    provider = build_provider(cfg.get("provider", {}), api_key=api_key)
    agents = {
        name: LLMAgent(name=name, provider=provider, **spec)
        for name, spec in cfg.get("agents", {}).items()
    }
    swarm = Swarm.from_config(cfg["swarm"], agents)
    return asyncio.run(swarm.run(task))


@app.command()
def run(
    task: str = typer.Argument(..., help="Task to execute"),
    config: Path = typer.Option(..., help="Path to swarm.yaml"),
    api_key: str | None = typer.Option(None, envvar="ANTHROPIC_API_KEY"),
    output: str = typer.Option("text", help="Output format: text | json | markdown"),
):
    """Run a swarm from a config file."""
    if not config.exists():
        typer.echo(f"Error: config file not found: {config}", err=True)
        raise typer.Exit(1)
    result = run_swarm(config, task, api_key=api_key)
    if output == "json":
        import json
        typer.echo(json.dumps({"output": result.final_output, "pattern": result.pattern}))
    elif output == "markdown":
        typer.echo(f"# Result\n\n{result.final_output}")
    else:
        typer.echo(result.final_output)


@app.command()
def init(
    output: Path = typer.Option(Path("swarm.yaml"), help="Output path for config file"),
):
    """Scaffold a swarm config file."""
    template = """\
provider:
  type: claude          # claude | ollama | litellm
  model: claude-sonnet-4-6
  auth_mode: subscription  # subscription (default) | api_key

agents:
  coordinator:
    system_prompt: "You are a coordinator. Break tasks into subtasks."
  worker:
    system_prompt: "You are a thorough researcher and writer."

swarm:
  - name: main
    pattern: sequential
    agents: [coordinator, worker]
"""
    output.write_text(template)
    typer.echo(f"Created {output}")


@app.command()
def validate(
    config: Path = typer.Option(..., help="Path to swarm.yaml"),
):
    """Validate a swarm config file without running it."""
    if not config.exists():
        typer.echo(f"Error: config file not found: {config}", err=True)
        raise typer.Exit(1)
    try:
        cfg = yaml.safe_load(config.read_text())
        if not isinstance(cfg, dict):
            typer.echo("Invalid: config must be a YAML mapping", err=True)
            raise typer.Exit(1)
        if "swarm" not in cfg:
            typer.echo("Invalid: missing 'swarm' key", err=True)
            raise typer.Exit(1)
        if "agents" not in cfg:
            typer.echo("Invalid: missing 'agents' key", err=True)
            raise typer.Exit(1)
        typer.echo(f"Config is valid: {len(cfg['swarm'])} swarm node(s), {len(cfg['agents'])} agent(s)")
    except yaml.YAMLError as e:
        typer.echo(f"Invalid YAML: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def export(
    output: Path = typer.Option(Path("swarm-export.yaml"), help="Output path"),
):
    """Export a swarm config skeleton (use from Python after building programmatically)."""
    typer.echo("Use Swarm().to_config() in Python and write to YAML.")


if __name__ == "__main__":
    app()
