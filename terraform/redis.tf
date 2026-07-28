# Enable the required APIs
resource "google_project_service" "vpcaccess_api" {
  project            = var.project_id
  service            = "vpcaccess.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "redis_api" {
  project            = var.project_id
  service            = "redis.googleapis.com"
  disable_on_destroy = false
}

# Private VPC Network
resource "google_compute_network" "fpa_vpc" {
  name                    = "fpa-vpc"
  auto_create_subnetworks = false
}

# Dedicated subnet for general compute (if needed in the future)
resource "google_compute_subnetwork" "fpa_subnet" {
  name          = "fpa-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.fpa_vpc.id
}

# Serverless VPC Access Connector
resource "google_vpc_access_connector" "connector" {
  name          = "fpa-vpc-connector"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28" # Small /28 block for connector IPs
  network       = google_compute_network.fpa_vpc.name

  depends_on = [google_project_service.vpcaccess_api]
}

# Memorystore Redis Instance
resource "google_redis_instance" "redis_cache" {
  name               = "fpa-redis-cache"
  tier               = "BASIC" # Basic Tier is optimal for development/staging workloads
  memory_size_gb     = 1
  region             = var.region
  authorized_network = google_compute_network.fpa_vpc.id
  connect_mode       = "DIRECT_PEERING"

  depends_on = [google_project_service.redis_api]
}
