resource "google_artifact_registry_repository" "fpa_repo" {
  location      = var.region
  repository_id = "fpa-repo"
  description   = "Docker repository for FP&A microservices"
  format        = "DOCKER"
}
