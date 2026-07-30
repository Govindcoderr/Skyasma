from graph.builder import WorkflowBuilder
from memory.checkpoint import get_checkpointer

from agents.state import create_initial_state


class Workflow:

    def __init__(self):
        self._graph = None
        self._checkpointer_cm = None

    async def _ensure_graph(self):
        if self._graph is None:
            self._checkpointer_cm = get_checkpointer()
            checkpointer = await self._checkpointer_cm.__aenter__()
            self._graph = WorkflowBuilder().build(checkpointer=checkpointer)
        return self._graph

    async def ainvoke(self, user_message: str, session_id: str = "default", thread_id: str = "default"):
        graph = await self._ensure_graph()

        state = create_initial_state(
            message=user_message, session_id=session_id, thread_id=thread_id
        )

        return await graph.ainvoke(
            state, config={"configurable": {"thread_id": thread_id}}
        )

    async def aclose(self):
        if self._checkpointer_cm:
            await self._checkpointer_cm.__aexit__(None, None, None)