resource "google_storage_bucket" "dataflow_storage" {
  name                        = "${var.project_id}-dataflow-storage"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30
    }
  }
}

resource "google_storage_bucket_iam_member" "dataflow_worker_bucket_access" {
  bucket = google_storage_bucket.dataflow_storage.name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.dataflow_worker.email}"
}

resource "google_storage_bucket_iam_member" "github_deployer_bucket_access" {
  bucket = google_storage_bucket.dataflow_storage.name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.github_deployer.email}"
}
