# tests/patterns/test_auction.py
import pytest
from swarm.patterns.auction import AuctionPattern
from swarm.core.types import AgentResult, SwarmContext
from swarm.core.errors import PatternError


class BiddingAgent:
    def __init__(self, name: str, bid: float) -> None:
        self.name = name
        self._bid = bid

    async def run(self, task, ctx):
        return AgentResult(agent_name=self.name, content=f"{self.name} wins", confidence=self._bid)


@pytest.fixture
def ctx():
    return SwarmContext()


async def test_auction_winner_has_highest_confidence(ctx):
    agents = [
        BiddingAgent("low", bid=0.3),
        BiddingAgent("high", bid=0.9),
        BiddingAgent("mid", bid=0.6),
    ]
    result = await AuctionPattern().execute(agents, "task", ctx)
    assert result.final_output == "high wins"
    assert result.pattern == "auction"


async def test_auction_requires_at_least_one_agent(ctx):
    with pytest.raises(PatternError):
        await AuctionPattern().execute([], "task", ctx)
