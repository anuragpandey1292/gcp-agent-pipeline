import os
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_ID", "superstore_analytics")
TABLE_ID = os.getenv("BQ_TABLE_ID", "superstore_sales")

client = bigquery.Client(project=PROJECT_ID)


def get_table_schema() -> str:
  """Returns the schema and column names of the superstore sales BigQuery table."""
  table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
  table = client.get_table(table_ref)
  schema_info = [f"{schema.name} ({schema.field_type})" for schema in table.schema]
  return f"Table `{table_ref}` schema: " + ", ".join(schema_info)


def execute_sql_query(query: str) -> list[dict]:
  """Executes a GoogleSQL read-only query against BigQuery and returns the rows as dictionaries."""
  # Enforce mutation guardrails
  forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
  if any(keyword in query.upper() for keyword in forbidden):
    return [{"error": "Mutation queries are forbidden. Only SELECT queries are permitted."}]

  try:
    query_job = client.query(query)
    results = query_job.result()
    rows = [dict(row) for row in results]
    # Return at most 50 rows to avoid context overload
    return rows[:50]
  except Exception as e:
    return [{"error": str(e)}]