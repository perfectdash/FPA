resource "google_sql_database_instance" "postgres" {
  name             = "fpa-budget-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-custom-1-3840" 
    
    ip_configuration {
      ipv4_enabled = true
    }
  }

  deletion_protection = false 

  depends_on = [google_project_service.enabled_apis["sqladmin.googleapis.com"]]
}

resource "google_sql_database" "budget_registry" {
  name     = "budget_registry"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "pgadmin" {
  name     = "pgadmin"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}
