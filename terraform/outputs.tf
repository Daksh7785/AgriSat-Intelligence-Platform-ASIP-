output "gke_cluster_name" {
  value = google_container_cluster.primary.name
}

output "db_instance_ip" {
  value = google_sql_database_instance.postgres_instance.public_ip_address
}

output "storage_bucket_url" {
  value = google_storage_bucket.raster_bucket.url
}
