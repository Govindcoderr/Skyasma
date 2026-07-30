from graph.builder import WorkflowBuilder

from agents.state import create_initial_state


class Workflow:

    def __init__(self):

        self.graph = WorkflowBuilder().build()

    def invoke(
        self,
        user_message: str,
    ):

        state = create_initial_state(
            message=user_message
        )

        return self.graph.invoke(state)