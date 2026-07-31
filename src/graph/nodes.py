import asyncio

from src.agents.supervisor import SupervisorAgent
from src.agents.planner import PlannerAgent
from src.agents.executor import ExecutorAgent
from src.agents.responder import ResponderAgent
from src.agents.state import AgentState


supervisor = SupervisorAgent()
planner = PlannerAgent()
executor = ExecutorAgent()
responder = ResponderAgent()


async def supervisor_node(state: AgentState):
    print("Running Supervisor...")
    return await asyncio.to_thread(supervisor, state)


async def planner_node(state: AgentState):
    print("Running Planner...")
    return await asyncio.to_thread(planner, state)


async def executor_node(state: AgentState):
    print("Running Executor...")
    return await executor(state)


async def responder_node(state: AgentState):
    print("Running Responder...")
    return await responder(state)