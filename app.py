from src.graph.workflow import Workflow

workflow = Workflow()

while True:

    text = input("User : ")

    if text.lower() == "exit":
        break

    result = workflow.invoke(text)

    print()

    print("Intent")

    print(result["intent"])

    print()

    print("Confidence")

    print(result["confidence"])

    print()

    print("Plan")

    for step in result["plan"]:

        print("-", step)

    print()