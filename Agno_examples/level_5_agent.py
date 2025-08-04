from typing import Iterator
from agno.agent import Agent, RunResponse
# from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from agno.utils.log import logger
from agno.utils.pprint import pprint_run_response
from agno.workflow import Workflow

from dotenv import load_dotenv
import os

load_dotenv("/Users/sandhiya.cv/Downloads/GenAI/sample/.env")


class CacheWorkflow(Workflow):
    # Add agents or teams as attributes on the workflow
    agent = Agent(model=Gemini(
        id=os.environ['DEFAULT_MODEL'],
        vertexai=os.environ['GOOGLE_GENAI_USE_VERTEXAI'],
        project_id=os.environ['GOOGLE_CLOUD_PROJECT'],
        location=os.environ['GOOGLE_CLOUD_LOCATION']
    ),)

    # Write the logic in the `run()` method
    def run(self, message: str) -> Iterator[RunResponse]:
        logger.info(f"Checking cache for '{message}'")
        # Check if the output is already cached
        if self.session_state.get(message):
            logger.info(f"Cache hit for '{message}'")
            yield RunResponse(
                run_id=self.run_id, content=self.session_state.get(message)
            )
            return

        logger.info(f"Cache miss for '{message}'")
        # Run the agent and yield the response
        yield from self.agent.run(message, stream=True)

        # Cache the output after response is yielded
        self.session_state[message] = self.agent.run_response.content


if __name__ == "__main__":
    workflow = CacheWorkflow()
    # Run workflow (this is takes ~1s)
    response: Iterator[RunResponse] = workflow.run(message="Tell me a joke.")
    # Print the response
    pprint_run_response(response, markdown=True, show_time=True)
    # Run workflow again (this is immediate because of caching)
    response: Iterator[RunResponse] = workflow.run(message="Tell me a joke.")
    # Print the response
    pprint_run_response(response, markdown=True, show_time=True)