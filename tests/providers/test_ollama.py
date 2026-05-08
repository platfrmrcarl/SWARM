import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from swarm.core.types import Message
from swarm.providers.ollama import OllamaProvider


def test_ollama_default_url():
    p = OllamaProvider(model="gemma3")
    assert p.base_url == "http://localhost:11434"


def test_ollama_custom_url():
    p = OllamaProvider(model="gemma3", base_url="http://remote:11434")
    assert p.base_url == "http://remote:11434"


@pytest.mark.asyncio
async def test_ollama_posts_to_api():
    p = OllamaProvider(model="gemma3")
    messages = [Message(role="user", content="hello")]
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "world"}}
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=mock_response)
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await p.complete(messages)
    assert result == "world"


@pytest.mark.asyncio
async def test_ollama_raises_on_http_error():
    p = OllamaProvider(model="gemma3")
    messages = [Message(role="user", content="hello")]
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(side_effect=Exception("Connection failed"))
    with patch("httpx.AsyncClient", return_value=mock_client):
        from swarm.core.errors import ProviderError
        with pytest.raises(ProviderError, match="Ollama error"):
            await p.complete(messages)
