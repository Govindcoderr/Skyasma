from langgraph.graph import StateGraph
from langgraph.graph import END

from src.agents.state import AgentState

from src.graph.nodes import supervisor_node, planner_node, executor_node, responder_node
from src.graph.router import route_after_supervisor, route_after_executor


class WorkflowBuilder:

    def build(self, checkpointer=None):

        graph = StateGraph(AgentState)

        graph.add_node("supervisor", supervisor_node)
        graph.add_node("planner", planner_node)
        graph.add_node("executor", executor_node)
        graph.add_node("responder", responder_node)

        graph.set_entry_point("supervisor")

        graph.add_conditional_edges(
            "supervisor",
            route_after_supervisor,
            {"planner": "planner", "responder": "responder"},
        )

        graph.add_edge("planner", "executor")

        graph.add_conditional_edges(
            "executor",
            route_after_executor,
            {"responder": "responder"},
        )

        graph.add_edge("responder", END)

        return graph.compile(checkpointer=checkpointer)