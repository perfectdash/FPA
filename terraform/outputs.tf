output "fastapi_ingester_service_account" {
  value       = google_service_account.fastapi_ingester.email
  description = "The email address of the ingestion service account."
}

output "dataflow_worker_service_account" {
  value       = google_service_account.dataflow_worker.email
  description = "The email address of the Dataflow worker service account."
}

output "fastapi_reporting_service_account" {
  value       = google_service_account.fastapi_reporting.email
  description = "The email address of the reporting service account."
}

output "db_connection_name" {
  value       = google_sql_database_instance.postgres.connection_name
  description = "The connection name of the PostgreSQL instance."
}

output "workload_identity_provider_name" {
  value       = google_iam_workload_identity_pool_provider.github_provider.name
  description = "The full identifier path of the GitHub Actions Workload Identity Provider."
}

output "artifact_registry_repository_url" {
  value       = "us-central1-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.fpa_repo.name}"
  description = "The repository URL for Artifact Registry Docker images."
}

output "dataflow_staging_bucket_name" {
  value       = google_storage_bucket.dataflow_storage.name
  description = "The name of the staging/temp bucket for Dataflow."
}

output "github_deployer_service_account_email" {
  value       = google_service_account.github_deployer.email
  description = "The email address of the GitHub Actions deployer service account."
}

