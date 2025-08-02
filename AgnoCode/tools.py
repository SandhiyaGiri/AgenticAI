from agno.agent import Agent
# from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.tools.yfinance import YFinanceTools
from dotenv import load_dotenv
import os

load_dotenv("/Users/sandhiya.cv/Downloads/GenAI/sample/.env")

agent = Agent(
    model=Gemini(
        id=os.environ['DEFAULT_MODEL'],
        vertexai=os.environ['GOOGLE_GENAI_USE_VERTEXAI'],
        project_id=os.environ['GOOGLE_CLOUD_PROJECT'],
        location=os.environ['GOOGLE_CLOUD_LOCATION']
    ),
    tools=[YFinanceTools(stock_price=True)],
    instructions="Use tables to display data. Don't include any other text.",
    markdown=True,
)
agent.print_response("What is the stock price of Apple, Microsoft, Google and Nvidia?", stream=True)
