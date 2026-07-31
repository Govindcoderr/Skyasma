import asyncio

from src.graph.workflow import Workflow


async def main():
    workflow = Workflow()

    try:
        while True:
            text = await asyncio.to_thread(input, "User : ")

            if text.lower() == "exit":
                break

            result = await workflow.ainvoke(text)

            print("\nIntent\n", result["intent"])
            print("\nConfidence\n", result["confidence"])
            print("\nPlan")
            for step in result["plan"]:
                print("-", step)
            print("\nFinal Response\n", result.get("final_response"), "\n")

    finally:
        await workflow.aclose()


if __name__ == "__main__":
    asyncio.run(main())