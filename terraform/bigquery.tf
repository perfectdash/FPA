resource "google_bigquery_dataset" "fpa_analytics" {
  dataset_id                  = "fpa_analytics"
  friendly_name               = "FP&A Analytics Dataset"
  description                 = "Contains transaction audit logs and windowed department budget aggregations."
  location                    = "US"
}

resource "google_bigquery_table" "transactions_raw" {
  dataset_id          = google_bigquery_dataset.fpa_analytics.dataset_id
  table_id            = "transactions_raw"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["department_id", "category"]

  schema = <<EOF
[
  {
    "name": "transaction_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "timestamp",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  },
  {
    "name": "department_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "amount",
    "type": "FLOAT",
    "mode": "REQUIRED"
  },
  {
    "name": "currency",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "category",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "vendor",
    "type": "STRING",
    "mode": "NULLABLE"
  }
]
EOF
}

resource "google_bigquery_table" "hourly_budget_aggregates" {
  
  dataset_id          = google_bigquery_dataset.fpa_analytics.dataset_id
  table_id            = "hourly_budget_aggregates"
  deletion_protection = false

  time_partitioning {
    type  = "HOUR"
    field = "window_start"
  }

  clustering = ["department_id"]

  schema = <<EOF
[
  {
    "name": "department_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "window_start",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  },
  {
    "name": "total_spend",
    "type": "FLOAT",
    "mode": "REQUIRED"
  },
  {
    "name": "budget_limit",
    "type": "FLOAT",
    "mode": "REQUIRED"
  },
  {
    "name": "variance",
    "type": "FLOAT",
    "mode": "REQUIRED"
  }
]
EOF
}

resource "google_bigquery_connection" "fpa_postgres" {
  connection_id = "fpa-postgres-connection"
  location      = "US"
  friendly_name = "FP&A Cloud SQL Connection"
  description   = "Link from BigQuery to Cloud SQL Postgres budget instance"
  cloud_sql {
    instance_id = google_sql_database_instance.postgres.connection_name
    database    = google_sql_database.budget_registry.name
    type        = "POSTGRES"
    credential {
      username = google_sql_user.pgadmin.name
      password = google_sql_user.pgadmin.password
    }
  }
}

