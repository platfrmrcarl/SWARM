from __future__ import annotations
from swarm.core.protocols import Pattern


def pattern_from_name(name: str, entry: dict) -> Pattern:
    name = name.lower()
    if name == "sequential":
        from swarm.patterns.sequential import SequentialPattern
        return SequentialPattern()
    if name == "parallel":
        from swarm.patterns.parallel import ParallelPattern
        return ParallelPattern(merge_strategy=entry.get("merge", "concatenate"))
    if name == "hierarchical":
        from swarm.patterns.hierarchical import HierarchicalPattern
        return HierarchicalPattern()
    if name == "decentralized":
        from swarm.patterns.decentralized import DecentralizedPattern
        return DecentralizedPattern()
    if name == "adaptive":
        from swarm.patterns.adaptive import AdaptivePattern
        return AdaptivePattern(
            threshold=entry.get("threshold", 0.8),
            max_hops=entry.get("max_hops", 5),
        )
    if name == "mesh":
        from swarm.patterns.mesh import MeshPattern
        return MeshPattern(max_rounds=entry.get("max_rounds", 5))
    if name in ("variant_judge", "variantjudge"):
        from swarm.patterns.variant_judge import VariantJudgePattern
        return VariantJudgePattern()
    if name == "reflection":
        from swarm.patterns.reflection import ReflectionPattern
        return ReflectionPattern(
            max_iterations=entry.get("max_iterations", 3),
        )
    if name == "broadcast":
        from swarm.patterns.broadcast import BroadcastPattern
        return BroadcastPattern()
    if name == "auction":
        from swarm.patterns.auction import AuctionPattern
        return AuctionPattern()
    if name in ("mixture_of_agents", "mixtureofagents", "moa"):
        from swarm.patterns.mixture_of_agents import MixtureOfAgentsPattern
        return MixtureOfAgentsPattern()
    if name == "debate":
        from swarm.patterns.debate import DebatePattern
        return DebatePattern(max_rounds=entry.get("max_rounds", 3))
    if name in ("tree_of_thoughts", "treeofthoughts", "tot"):
        from swarm.patterns.tree_of_thoughts import TreeOfThoughtsPattern
        return TreeOfThoughtsPattern(
            max_depth=entry.get("max_depth", 3),
            branching_factor=entry.get("branching_factor", 2),
        )
    if name == "speculative":
        from swarm.patterns.speculative import SpeculativePattern
        return SpeculativePattern(threshold=entry.get("threshold", 0.8))
    if name == "blackboard":
        from swarm.patterns.blackboard import BlackboardPattern
        return BlackboardPattern(max_rounds=entry.get("max_rounds", 5))
    raise ValueError(f"Unknown pattern: {name!r}")


def build_provider(provider_cfg: dict, api_key: str | None = None):
    ptype = provider_cfg.get("type", "claude")
    model = provider_cfg.get("model", "claude-sonnet-4-6")
    if ptype == "claude":
        from swarm.providers.claude import ClaudeProvider
        auth_mode = provider_cfg.get("auth_mode", "subscription")
        key = api_key if auth_mode == "api_key" else None
        return ClaudeProvider(model=model, api_key=key)
    if ptype == "ollama":
        from swarm.providers.ollama import OllamaProvider
        return OllamaProvider(model=model, base_url=provider_cfg.get("base_url", "http://localhost:11434"))
    if ptype == "litellm":
        from swarm.providers.litellm import LiteLLMProvider
        return LiteLLMProvider(model=model)
    raise ValueError(f"Unknown provider type: {ptype!r}")
