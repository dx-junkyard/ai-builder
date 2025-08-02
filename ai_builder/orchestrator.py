"""Orchestrator module implementing LangGraph pipeline."""

from typing import Any, Callable
from langgraph import StateGraph, END
from ai_builder import generator, evaluator, runtime_pool


def build_graph() -> Any:
    """Build the LangGraph for agent generation and deployment.

    Returns:
        Compiled LangGraph object.
    """
    graph = StateGraph()
    graph.add_node("Generate", generator.build_agent)
    graph.add_node("Evaluate", evaluator.run_suite)
    graph.add_node("Deploy", runtime_pool.deploy)

    graph.set_entry("Generate")
    graph.connect("Generate", "Evaluate")
    graph.connect("Evaluate", condition=lambda score: score >= 0.8, true="Deploy", false="Generate")
    graph.set_termination("Deploy", END)
    return graph.compile()

