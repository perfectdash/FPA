import argparse
import json
import logging
import time
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions
from apache_beam.transforms.trigger import AfterWatermark, AfterCount, Repeatedly
from apache_beam.window import FixedWindows, TimestampedValue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fpa_pipeline")

class ParseTransactionFn(beam.DoFn):
    """Parses JSON transactions and enforces data schema type casting."""
    def process(self, element):
        try:
            if isinstance(element, bytes):
                raw_str = element.decode("utf-8")
            else:
                raw_str = str(element)
            data = json.loads(raw_str)
            parsed = {
                "transaction_id": str(data.get("transaction_id") or data.get("transactionId")),
                "timestamp": str(data["timestamp"]),
                "department_id": str(data.get("department_id") or data.get("departmentId")),
                "amount": float(data["amount"]),
                "currency": str(data["currency"]),
                "category": str(data["category"]),
                "vendor": str(data["vendor"]),
            }
            yield parsed
        except Exception as e:
            logger.error(f"Error parsing transaction record: {e}. Raw data: {element}")
            yield beam.pvalue.TaggedOutput("dead_letter", element)

class BudgetComplianceCheckFn(beam.DoFn):
    """Compares the current window aggregations against department budgets loaded from Cloud SQL."""
    def __init__(self, db_instance_connection_name, db_name="budget_registry", db_user="pgadmin", db_password=None):
        self.db_instance_connection_name = db_instance_connection_name
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        
        # Runtime cache
        self.budgets_cache = {}
        self.last_fetch_time = 0
        self.ttl_seconds = 300 # 5 minutes

    def setup(self):
        """Initializes the database connection pool."""
        if not self.db_instance_connection_name or not self.db_password:
            raise ValueError("Database connection details and password must be provided to run the pipeline.")
        try:
            from google.cloud.sql.connector import Connector
            import sqlalchemy
            
            self.connector = Connector()
            
            def getconn():
                return self.connector.connect(
                    self.db_instance_connection_name,
                    "pg8000",
                    user=self.db_user,
                    password=self.db_password,
                    db=self.db_name
                )
            
            self.db_pool = sqlalchemy.create_engine(
                "postgresql+pg8000://",
                creator=getconn,
            )
            logger.info(f"Database connection pool initialized targeting {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise e

    def teardown(self):
        """Clean up the database connector when the worker shuts down."""
        if hasattr(self, "connector"):
            try:
                self.connector.close()
            except Exception:
                pass

    def _refresh_budgets_if_needed(self):
        """Refreshes the local budgets cache from Cloud SQL if the TTL has expired."""
        import time
        current_time = time.time()
        
        # If cache is valid, skip database query
        if current_time - self.last_fetch_time < self.ttl_seconds and self.budgets_cache:
            return

        if not hasattr(self, "db_pool") or self.db_pool is None:
            raise RuntimeError("Database connection pool is not initialized.")

        try:
            import sqlalchemy
            logger.info("Fetching department budgets from Cloud SQL...")
            with self.db_pool.connect() as conn:
                result = conn.execute(sqlalchemy.text("SELECT department_id, allocated_budget FROM department_budgets"))
                new_cache = {}
                for row in result:
                    new_cache[row[0]] = float(row[1])
                if new_cache:
                    self.budgets_cache = new_cache
                    self.last_fetch_time = current_time
                    logger.info(f"Successfully refreshed budgets from DB: {self.budgets_cache}")
                    return
        except Exception as e:
            logger.error(f"Error querying budget registry from Cloud SQL: {e}")
            if not self.budgets_cache:
                raise e

    def process(self, element, window=beam.DoFn.WindowParam):
        dep_id, amount_spent = element
        
        # Refresh the cache if TTL has expired
        self._refresh_budgets_if_needed()
        
        # Get budget limit from cache (defaults to $100k if not found)
        budget_limit = self.budgets_cache.get(dep_id, 100000.0)
        
        window_start = "unknown"
        if window is not None:
            try:
                window_start = window.start.to_utc_datetime().isoformat() + "Z"
            except Exception:
                pass
                
        if amount_spent > budget_limit:
            alert = {
                "department_id": dep_id,
                "window_start": window_start,
                "amount_spent": amount_spent,
                "budget_limit": budget_limit,
                "variance": round(amount_spent - budget_limit, 2),
                "status": "BUDGET_BREACH"
            }
            logger.warning(f"BUDGET BREACH detected: {alert}")
            yield alert


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_subscription",
        default="projects/google-corp-eng-fpa/subscriptions/transactions-sub",
        help="Pub/Sub subscription to pull from in GCP mode."
    )
    parser.add_argument(
        "--output_table",
        default="google-corp-eng-fpa:fpa_analytics.transactions_raw",
        help="BigQuery table spec: PROJECT:DATASET.TABLE"
    )
    parser.add_argument(
        "--alerts_topic",
        default="projects/google-corp-eng-fpa/topics/budget-breaches-alerts",
        help="Pub/Sub topic to write budget breach alerts to."
    )
    parser.add_argument(
        "--db_instance_connection_name",
        default=None,
        help="GCP Cloud SQL instance connection name (e.g. project:region:instance)."
    )
    parser.add_argument(
        "--db_name",
        default="budget_registry",
        help="PostgreSQL database name."
    )
    parser.add_argument(
        "--db_user",
        default="pgadmin",
        help="PostgreSQL user name."
    )
    parser.add_argument(
        "--db_password",
        default=None,
        help="PostgreSQL password."
    )
    known_args, pipeline_args = parser.parse_known_args(argv)
    
    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = True
    
    from apache_beam.options.pipeline_options import StandardOptions
    pipeline_options.view_as(StandardOptions).streaming = True
    
    logger.info("Starting GCP-STREAMING Beam pipeline...")
    with beam.Pipeline(options=pipeline_options) as p:
        raw_stream = p | "Read From PubSub" >> beam.io.ReadFromPubSub(
            subscription=known_args.input_subscription
        )
        
        parsed_data = raw_stream | "Parse JSON" >> beam.ParDo(ParseTransactionFn()).with_outputs(
            "dead_letter",
            main="clean_data"
        )
        clean_transactions = parsed_data.clean_data
        dead_letters = parsed_data.dead_letter
        dead_letters | "Log Malformed Messages" >> beam.Map(lambda x: logger.error(f"Malformed: {x}"))
        
        clean_transactions | "Write Raw to BQ" >> beam.io.WriteToBigQuery(
            known_args.output_table,
            schema="transaction_id:STRING, timestamp:TIMESTAMP, department_id:STRING, amount:FLOAT, currency:STRING, category:STRING, vendor:STRING",
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
        )
        
        windowed_transactions = (
            clean_transactions
            | "Extract Event Timestamps" >> beam.Map(
                lambda x: TimestampedValue(x, float(x["timestamp"]))
            )
            | "Hourly Tumbling Window" >> beam.WindowInto(
                FixedWindows(3600),
                trigger=Repeatedly(AfterWatermark(early=AfterCount(5))),
                accumulation_mode=beam.transforms.trigger.AccumulationMode.ACCUMULATING
            )
        )
        
        windowed_sums = (
            windowed_transactions
            | "Map Key-Value (Dep, Amount)" >> beam.Map(lambda x: (x["department_id"], x["amount"]))
            | "Combine Per Department" >> beam.CombinePerKey(sum)
        )
        
        breaches = windowed_sums | "Evaluate Compliance" >> beam.ParDo(
            BudgetComplianceCheckFn(
                db_instance_connection_name=known_args.db_instance_connection_name,
                db_name=known_args.db_name,
                db_user=known_args.db_user,
                db_password=known_args.db_password
            )
        )
        
        (
            breaches
            | "Encode Alerts JSON" >> beam.Map(lambda x: json.dumps(x).encode("utf-8"))
            | "Publish Alerts to PubSub" >> beam.io.WriteToPubSub(topic=known_args.alerts_topic)
        )


if __name__ == "__main__":
    run()

