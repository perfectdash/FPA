resource "google_service_account" "fastapi_ingester" {
  account_id   = "fastapi-ingester"
  display_name = "FastAPI Ingestion Service Account"

  depends_on = [google_project_service.enabled_apis["iam.googleapis.com"]]
}

resource "google_service_account" "dataflow_worker" {
  account_id   = "dataflow-worker"
  display_name = "Dataflow Pipeline Worker Service Account"

  depends_on = [google_project_service.enabled_apis["iam.googleapis.com"]]
}

resource "google_service_account" "fastapi_reporting" {
  account_id   = "fastapi-reporting"
  display_name = "FastAPI Reporting API Service Account"

  depends_on = [google_project_service.enabled_apis["iam.googleapis.com"]]
}

resource "google_project_iam_member" "ingester_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.fastapi_ingester.email}"
}

resource "google_project_iam_member" "dataflow_roles" {
  for_each = toset([
    "roles/dataflow.worker",
    "roles/pubsub.subscriber",
    "roles/pubsub.publisher",
    "roles/pubsub.viewer",
    "roles/bigquery.dataEditor",
    "roles/cloudsql.client",
    "roles/artifactregistry.reader"
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.dataflow_worker.email}"
}

resource "google_project_iam_member" "reporting_roles" {
  for_each = toset([
    "roles/bigquery.dataViewer",
    "roles/bigquery.jobUser",
    "roles/bigquery.connectionUser"
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.fastapi_reporting.email}"
}

resource "google_service_account" "fastapi_frontend" {
  account_id   = "fastapi-frontend"
  display_name = "FastAPI Frontend Service Account"

  depends_on = [google_project_service.enabled_apis["iam.googleapis.com"]]
}
