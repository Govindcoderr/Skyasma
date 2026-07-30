import asyncio

from agents.supervisor import SupervisorAgent
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.responder import ResponderAgent
from agents.state import AgentState


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