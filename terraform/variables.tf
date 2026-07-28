variable "project_id" {
  type        = string
  description = "The Google Cloud Platform Project ID."
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "Default deployment region for GCP resources."
}

variable "zone" {
  type        = string
  default     = "us-central1-a"
  description = "Default compute zone for SQL and Dataflow VM targets."
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "The password for the PostgreSQL administrator user."
}

variable "github_repository" {
    type = string
    description = "The GitHub repository"
    default = "perfectdash/FPA"
}