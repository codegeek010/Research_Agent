from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from state import ResearchState
from agent import ResearchAgent


def _build_graph() -> StateGraph:
    agent = ResearchAgent()

    def fan_out(state: ResearchState) -> list[Send]:
        return [Send("researcher_node", {"section": s}) for s in state["sections"]]

    def route_decision(state: ResearchState) -> str:
        return "greeter_node" if state["input_type"] == "greeting" else "planner_node"

    graph = StateGraph(ResearchState)

    graph.add_node("router_node", agent.router_node)
    graph.add_node("greeter_node", agent.greeter_node)
    graph.add_node("planner_node", agent.planner_node)
    graph.add_node("researcher_node", agent.researcher_node)
    graph.add_node("writer_node", agent.writer_node)

    graph.add_edge(START, "router_node")
    graph.add_conditional_edges(
        "router_node", route_decision,
        {"greeter_node": "greeter_node", "planner_node": "planner_node"},
    )
    graph.add_edge("greeter_node", END)
    graph.add_conditional_edges("planner_node", fan_out, ["researcher_node"])
    graph.add_edge("researcher_node", "writer_node")
    graph.add_edge("writer_node", END)

    return graph.compile()


_research_graph = _build_graph()


def get_mermaid() -> str:
    return _research_graph.get_graph().draw_mermaid()


_STREAMING_NODES = {"greeter_node", "writer_node"}


def _initial_state(user_message: str) -> dict:
    return {
        "user_message": user_message,
        "topic": "",
        "input_type": "",
        "sections": [],
        "briefs": [],
        "report": "",
        "output": "",
    }


def stream_with_status(user_message: str):
    researcher_done = 0
    total_sections = 0

    for event_type, event_data in _research_graph.stream(
        _initial_state(user_message),
        stream_mode=["updates", "messages"],
    ):
        if event_type == "updates":
            node = list(event_data.keys())[0]
            if node == "router_node" and event_data["router_node"].get("input_type") == "topic":
                yield "status", "📋 Planning research sections..."
            elif node == "planner_node":
                total_sections = len(event_data["planner_node"].get("sections", []))
                yield "status", f"🔍 Searching {total_sections} topics..."
            elif node == "researcher_node":
                researcher_done += 1
                yield "status", f"🔍 Analysed {researcher_done}/{total_sections} sections..."

        elif event_type == "messages":
            chunk, metadata = event_data
            if (
                hasattr(chunk, "content")
                and chunk.content
                and metadata.get("langgraph_node") in _STREAMING_NODES
            ):
                yield "token", chunk.content
