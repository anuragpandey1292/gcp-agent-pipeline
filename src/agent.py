import os
from dotenv import load_dotenv
from google.adk import Agent
from src.tools import execute_sql_query, get_table_schema

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_ID", "superstore_analytics")
TABLE_ID = os.getenv("BQ_TABLE_ID", "superstore_sales")
FULL_TABLE_NAME = f"`{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`"

SYSTEM_INSTRUCTION = """
You are an expert Superstore Data Analyst.
- If the user greets you or asks general questions, reply politely and concisely without calling any tools.
- When the user asks analytical or data-related questions about sales, profit, orders, or categories, use the available tools (`get_table_schema` and `execute_sql_query`) to query the BigQuery table `superstore_analytics.superstore_sales`.


Operational Guidelines:
1. Always call `get_table_schema` first if you do not know the exact column names.
2. Formulate standard GoogleSQL queries using valid syntax. Always enclose table names in backticks.
3. Use `execute_sql_query` to fetch data.
4. Summarize results clearly with business context (totals, margins, averages, anomalies).
5. Never perform any write or mutation operations.
"""

root_agent = Agent(
    name="superstore_analyst_agent",
    model="gemini-3.5-flash",
    instruction=SYSTEM_INSTRUCTION,
    tools=[get_table_schema, execute_sql_query],
)