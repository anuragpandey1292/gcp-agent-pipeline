import os
from dotenv import load_dotenv
from google.cloud import bigquery, storage

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
DATASET_ID = os.getenv("BQ_DATASET_ID", "superstore_analytics")
TABLE_ID = os.getenv("BQ_TABLE_ID", "superstore_sales")
CSV_PATH = "data/superstore_sales.csv"
BLOB_NAME = "raw/superstore_sales.csv"


def create_bucket_if_not_exists(storage_client: storage.Client, bucket_name: str):
  bucket = storage_client.bucket(bucket_name)
  if not bucket.exists():
    bucket = storage_client.create_bucket(bucket_name, location="US")
    print(f"Created bucket: {bucket_name}")
  else:
    print(f"Bucket {bucket_name} already exists.")
  return bucket


def upload_to_gcs(
    storage_client: storage.Client, bucket_name: str, source_file: str, destination_blob: str
):
  bucket = storage_client.bucket(bucket_name)
  blob = bucket.blob(destination_blob)
  blob.upload_from_filename(source_file)
  print(f"Uploaded {source_file} to gs://{bucket_name}/{destination_blob}")
  return f"gs://{bucket_name}/{destination_blob}"


def load_gcs_to_bigquery(
    bq_client: bigquery.Client, gcs_uri: str, dataset_id: str, table_id: str
):
  dataset_ref = bigquery.DatasetReference(PROJECT_ID, dataset_id)
  dataset = bigquery.Dataset(dataset_ref)
  dataset.location = "US"
  bq_client.create_dataset(dataset, exists_ok=True)
  print(f"Ensured dataset exists: {dataset_id}")

  table_ref = dataset_ref.table(table_id)
  job_config = bigquery.LoadJobConfig(
      source_format=bigquery.SourceFormat.CSV,
      skip_leading_rows=1,
      autodetect=True,
      write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
  )

  load_job = bq_client.load_table_from_uri(gcs_uri, table_ref, job_config=job_config)
  print(f"Starting BigQuery load job {load_job.job_id}...")
  load_job.result()  # Wait for the load job to complete

  destination_table = bq_client.get_table(table_ref)
  print(
      f"Loaded {destination_table.num_rows} rows into {PROJECT_ID}.{dataset_id}.{table_id}."
  )


if __name__ == "__main__":
  if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"File not found: {CSV_PATH}. Place your CSV inside data/.")

  storage_client = storage.Client(project=PROJECT_ID)
  bq_client = bigquery.Client(project=PROJECT_ID)

  create_bucket_if_not_exists(storage_client, BUCKET_NAME)
  gcs_uri = upload_to_gcs(storage_client, BUCKET_NAME, CSV_PATH, BLOB_NAME)
  load_gcs_to_bigquery(bq_client, gcs_uri, DATASET_ID, TABLE_ID)
  print("Ingestion pipeline finished successfully.")