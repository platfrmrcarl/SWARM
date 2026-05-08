from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from swarm.cli.main import app

runner = CliRunner()


def test_init_creates_config_file(tmp_path):
    result = runner.invoke(app, ["init", "--output", str(tmp_path / "swarm.yaml")])
    assert result.exit_code == 0
    assert (tmp_path / "swarm.yaml").exists()


def test_validate_valid_config(tmp_path):
    config = tmp_path / "swarm.yaml"
    config.write_text(
        "provider:\n  type: claude\nagents:\n  worker:\n    system_prompt: You are a worker.\nswarm:\n  - name: s1\n    pattern: sequential\n    agents: [worker]\n"
    )
    result = runner.invoke(app, ["validate", "--config", str(config)])
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_validate_invalid_config(tmp_path):
    config = tmp_path / "bad.yaml"
    config.write_text("not: yaml: config")
    result = runner.invoke(app, ["validate", "--config", str(config)])
    assert result.exit_code != 0 or "error" in result.output.lower() or "invalid" in result.output.lower()


def test_run_command_invokes_swarm(tmp_path):
    config = tmp_path / "swarm.yaml"
    config.write_text(
        "provider:\n  type: claude\nagents:\n  worker:\n    system_prompt: You are a worker.\nswarm:\n  - name: s1\n    pattern: sequential\n    agents: [worker]\n"
    )
    mock_result = MagicMock()
    mock_result.final_output = "test output"
    with patch("swarm.cli.main.run_swarm", return_value=mock_result):
        result = runner.invoke(
            app, ["run", "--config", str(config), "do a task"]
        )
    assert result.exit_code == 0
