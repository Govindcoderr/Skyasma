from agents.supervisor import SupervisorAgent
from agents.planner import PlannerAgent
from agents.state import AgentState


supervisor = SupervisorAgent()
planner = PlannerAgent()


def supervisor_node(state: AgentState):

    print("Running Supervisor...")

    return supervisor(state)


def planner_node(state: AgentState):

    print("Running Planner...")

    return planner(state)