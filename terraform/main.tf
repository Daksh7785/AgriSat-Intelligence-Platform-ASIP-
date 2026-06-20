provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Cloud Storage Bucket for Satellite Rasters
resource "google_storage_bucket" "raster_bucket" {
  name          = "${var.project_id}-satellite-rasters"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# 2. Cloud SQL PostgreSQL instance (PostGIS enabled)
resource "google_sql_database_instance" "postgres_instance" {
  name             = "agrisense-db-instance"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro" # Demo scale; upgrade for production scale
    
    ip_configuration {
      ipv4_enabled    = true
      authorized_networks {
        name  = "all"
        value = "0.0.0.0/0"
      }
    }
  }
}

resource "google_sql_database" "database" {
  name     = "agrisense"
  instance = google_sql_database_instance.postgres_instance.name
}

# 3. Google Kubernetes Engine (GKE) Cluster
resource "google_container_cluster" "primary" {
  name     = "agrisense-gke-cluster"
  location = var.region

  remove_default_node_pool = true
  initial_node_count       = 1
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "agrisense-node-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = 2

  node_config {
    preemptible  = true
    machine_type = "e2-medium"

    metadata = {
      disable-legacy-endpoints = "true"
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}
