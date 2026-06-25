"""LangGraph state graph for checkin agent."""
from __future__ import annotations

from langgraph.graph import StateGraph, END

from services.agent.graph.state import GraphState
from services.agent.graph.nodes.retrieve_context import retrieve_context_node
from services.agent.graph.nodes.preference_extractor import preference_extractor_node
from services.agent.graph.nodes.hard_filter import hard_filter_node
from services.agent.graph.nodes.scorer import scorer_node
from services.agent.graph.nodes.conflict_detector import conflict_detector_node
from services.agent.graph.nodes.reason_builder import reason_builder_node
from services.agent.graph.nodes.llm_explainer import llm_explainer_node
from services.agent.graph.nodes.locker import locker_node
from services.agent.graph.nodes.checkin_completer import checkin_completer_node


def _route_entry(state: GraphState) -> str:
    """Route from entry point based on status."""
    status = state.get("status", "")
    if status == "recommended":
        return "lock"
    if status == "reseating":
        return "hard_filter"
    if status == "clarifying":
        return "clarify"
    return "retrieve_context"


def _route_after_detect(state: GraphState) -> str:
    """Route after conflict detection: clarify, exhausted, or continue."""
    status = state.get("status", "")
    if status == "clarifying":
        return "clarify"
    if status == "exhausted":
        return END
    return "build_reason"


def _route_after_lock(state: GraphState) -> str:
    """Route after lock: reseat, exhausted, or complete."""
    if state.get("status") == "exhausted":
        return END
    if state.get("status") == "reseating":
        return "hard_filter"
    return "complete"


def build_graph():
    """Build and compile the LangGraph state graph."""
    workflow = StateGraph(GraphState)

    # Register all nodes
    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("extract_preferences", preference_extractor_node)
    workflow.add_node("hard_filter", hard_filter_node)
    workflow.add_node("score", scorer_node)
    workflow.add_node("detect_conflicts", conflict_detector_node)
    workflow.add_node("build_reason", reason_builder_node)
    workflow.add_node("explain", llm_explainer_node)
    workflow.add_node("lock", locker_node)
    workflow.add_node("complete", checkin_completer_node)
    workflow.add_node("clarify", lambda state: {**state, "next_action": "end"})

    # Entry point with conditional routing
    workflow.add_node("entry_router", lambda state: state)
    workflow.set_entry_point("entry_router")
    workflow.add_conditional_edges(
        "entry_router",
        _route_entry,
        {
            "retrieve_context": "retrieve_context",
            "lock": "lock",
            "hard_filter": "hard_filter",
            "clarify": "clarify",
        },
    )

    # Route from retrieve_context: END on error, otherwise continue
    workflow.add_conditional_edges(
        "retrieve_context",
        lambda state: END if state.get("status") == "error" else "extract_preferences",
        {"extract_preferences": "extract_preferences", END: END},
    )

    # Route to END on extraction error, otherwise continue
    workflow.add_conditional_edges(
        "extract_preferences",
        lambda state: END if state.get("status") == "error" else "hard_filter",
        {"hard_filter": "hard_filter", END: END},
    )
    workflow.add_edge("hard_filter", "score")
    workflow.add_edge("score", "detect_conflicts")

    # Conditional routing after conflict detection
    workflow.add_conditional_edges(
        "detect_conflicts",
        _route_after_detect,
        {
            "build_reason": "build_reason",
            "clarify": "clarify",
            END: END,
        },
    )

    workflow.add_edge("build_reason", "explain")
    workflow.add_edge("explain", "lock")

    # Conditional routing after lock attempt
    workflow.add_conditional_edges(
        "lock",
        _route_after_lock,
        {
            "hard_filter": "hard_filter",
            "complete": "complete",
            END: END,
        },
    )

    workflow.add_edge("complete", END)
    workflow.add_edge("clarify", END)

    return workflow.compile()


__all__ = ["build_graph"]