resource "google_artifact_registry_repository" "fpa_repo" {
  location      = var.region
  repository_id = "fpa-repo"
  description   = "Docker repository for FP&A microservices"
  format        = "DOCKER"

  depends_on = [google_project_service.enabled_apis["artifactregistry.googleapis.com"]]
}
