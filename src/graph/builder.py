from langgraph.graph import StateGraph
from langgraph.graph import END

from agents.state import AgentState

from graph.nodes import (
    supervisor_node,
    planner_node,
)


class WorkflowBuilder:

    def build(self):

        graph = StateGraph(AgentState)

        #################################################
        # Nodes
        #################################################

        graph.add_node(
            "supervisor",
            supervisor_node,
        )

        graph.add_node(
            "planner",
            planner_node,
        )

        #################################################
        # Flow
        #################################################

        graph.set_entry_point("supervisor")

        graph.add_edge(
            "supervisor",
            "planner",
        )

        graph.add_edge(
            "planner",
            END,
        )

        return graph.compile()