output "vm_public_ip" {
  description = "Public IP of the gallery VM."
  value       = google_compute_instance.gallery.network_interface[0].access_config[0].nat_ip
}

output "app_url" {
  description = "URL to open in a browser once the startup script finishes (~2-3 min after apply)."
  value       = "http://${google_compute_instance.gallery.network_interface[0].access_config[0].nat_ip}/"
}

output "health_url" {
  description = "Health check endpoint. Should return 200 OK once gunicorn is up."
  value       = "http://${google_compute_instance.gallery.network_interface[0].access_config[0].nat_ip}/health"
}

output "db_private_ip" {
  description = "Private IP of the Cloud SQL instance (only reachable from inside the VPC)."
  value       = google_sql_database_instance.mysql.private_ip_address
}

output "db_connection_name" {
  description = "Cloud SQL connection name (for gcloud sql connect / Cloud SQL Auth Proxy)."
  value       = google_sql_database_instance.mysql.connection_name
}

output "gcs_photo_bucket_name" {
  description = "GCS bucket where uploaded photos are stored."
  value       = google_storage_bucket.photos.name
}

output "gcs_deploy_bucket_name" {
  description = "GCS bucket where the app tarball is uploaded for the VM startup script."
  value       = google_storage_bucket.deploy.name
}

output "service_account_email" {
  description = "Email of the VM's attached service account."
  value       = google_service_account.gallery_vm.email
}

output "ssh_command" {
  description = "Convenience SSH command for the VM."
  value       = "gcloud compute ssh ${google_compute_instance.gallery.name} --zone=${var.zone} --project=${var.project_id}"
}
