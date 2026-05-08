import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swarm.core.errors import ProviderError
from swarm.core.types import Message
from swarm.providers.claude import ClaudeProvider


def test_subscription_mode_is_default():
    p = ClaudeProvider(model="claude-sonnet-4-6")
    assert p.auth_mode == "subscription"


def test_api_key_mode_sets_auth():
    p = ClaudeProvider(model="claude-sonnet-4-6", api_key="sk-ant-test")
    assert p.auth_mode == "api_key"


@pytest.mark.asyncio
async def test_subscription_calls_subprocess():
    p = ClaudeProvider(model="claude-sonnet-4-6")
    messages = [Message(role="user", content="hello")]
    mock_result = MagicMock()
    mock_result.stdout = "world"
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = await p.complete(messages)
    assert result == "world"
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "claude"
    assert "-p" in args


@pytest.mark.asyncio
async def test_api_key_calls_anthropic():
    messages = [Message(role="user", content="hello")]
    mock_client = AsyncMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="world")]
    )
    with patch("swarm.providers.claude.AsyncAnthropic", return_value=mock_client):
        p = ClaudeProvider(model="claude-sonnet-4-6", api_key="sk-ant-test")
        result = await p.complete(messages)
    assert result == "world"


@pytest.mark.asyncio
async def test_subscription_raises_on_nonzero_exit():
    p = ClaudeProvider(model="claude-sonnet-4-6")
    messages = [Message(role="user", content="hello")]
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "command not found"
    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(ProviderError, match="claude CLI error"):
            await p.complete(messages)
