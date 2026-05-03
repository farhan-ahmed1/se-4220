// =============================================================================
// PHOTOGALLERY - SE 4220 FINAL PROJECT
// =============================================================================
// One-file infrastructure for the gallery app. Sections:
//   1. Provider
//   2. Networking (VPC, subnet, firewall, private services connection)
//   3. Cloud SQL (MySQL, private IP)
//   4. GCS buckets (photos + deploy tarball)
//   5. IAM (service account + least-privilege role bindings)
//   6. Compute Engine VM (startup script bootstraps the app)
// =============================================================================

// ----- 1. Provider ----------------------------------------------------------

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

// Random suffix keeps GCS bucket names globally unique across re-applies.
resource "random_id" "suffix" {
  byte_length = 3
}

locals {
  name = var.name_prefix
}

// ----- 2. Networking --------------------------------------------------------

resource "google_compute_network" "vpc" {
  name                    = "${local.name}-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${local.name}-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
}

// Allow HTTP/HTTPS to any VM tagged "gallery-web".
resource "google_compute_firewall" "web" {
  name      = "${local.name}-allow-web"
  network   = google_compute_network.vpc.name
  direction = "INGRESS"

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["gallery-web"]
}

resource "google_compute_firewall" "ssh" {
  name      = "${local.name}-allow-ssh"
  network   = google_compute_network.vpc.name
  direction = "INGRESS"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = var.ssh_source_ranges
  target_tags   = ["gallery-web"]
}

// Private Services Access: required so Cloud SQL can sit on a private IP
// inside our VPC. GCP allocates a /16 from this range for managed services.
resource "google_compute_global_address" "private_ip_range" {
  name          = "${local.name}-google-services-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
}

// ----- 3. Cloud SQL ---------------------------------------------------------

resource "google_sql_database_instance" "mysql" {
  name             = "${local.name}-mysql-${random_id.suffix.hex}"
  database_version = "MYSQL_8_0"
  region           = var.region

  // Cloud SQL must wait for the private services connection to exist,
  // otherwise it cannot allocate a private IP.
  depends_on = [google_service_networking_connection.private_vpc_connection]

  settings {
    tier = var.db_tier

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }

    backup_configuration {
      enabled = false
    }
  }

  // Allows `terraform destroy` to remove the instance without manual unprotect.
  deletion_protection = false
}

resource "google_sql_database" "app_db" {
  name     = var.db_name
  instance = google_sql_database_instance.mysql.name
}

resource "google_sql_user" "app_user" {
  name     = var.db_user
  instance = google_sql_database_instance.mysql.name
  host     = "%"
  password = var.db_password
}

// ----- 4. GCS buckets -------------------------------------------------------

// Public-read bucket for uploaded photos. The app writes objects here and
// stores their public URL in MySQL.
resource "google_storage_bucket" "photos" {
  name                        = "${local.name}-photos-${random_id.suffix.hex}"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
}

// Make every uploaded photo publicly readable so <img src="..."> just works.
resource "google_storage_bucket_iam_member" "photos_public_read" {
  bucket = google_storage_bucket.photos.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

// Private bucket: holds the app source tarball that the VM downloads at boot.
resource "google_storage_bucket" "deploy" {
  name                        = "${local.name}-deploy-${random_id.suffix.hex}"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
}

// Package the Flask app source. Excludes terraform/, venvs, secrets, caches.
data "archive_file" "app" {
  type        = "zip"
  source_dir  = var.app_source_dir != "" ? var.app_source_dir : "${path.module}/.."
  output_path = "${path.module}/dist/app.zip"

  excludes = [
    "terraform",
    ".venv",
    "venv",
    "__pycache__",
    "static/media",
    "gcp-key.json",
    ".env",
    ".env.gcp",
    ".gcloudignore",
  ]
}

resource "google_storage_bucket_object" "app_archive" {
  name   = "app-${data.archive_file.app.output_md5}.zip"
  bucket = google_storage_bucket.deploy.name
  source = data.archive_file.app.output_path
}

// Schema lives outside the app archive (terraform/ is excluded above), so
// upload it separately and let the startup script fetch it.
resource "google_storage_bucket_object" "schema_sql" {
  name   = "schema-${filemd5("${path.module}/schema.sql")}.sql"
  bucket = google_storage_bucket.deploy.name
  source = "${path.module}/schema.sql"
}

// ----- 5. IAM ---------------------------------------------------------------

resource "google_service_account" "gallery_vm" {
  account_id   = "${local.name}-vm-sa"
  display_name = "Photogallery VM service account"
}

// Read-only on the deploy bucket so the VM can fetch its own source code.
resource "google_storage_bucket_iam_member" "vm_deploy_read" {
  bucket = google_storage_bucket.deploy.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.gallery_vm.email}"
}

// Read/write on the photos bucket so the app can upload new photos.
resource "google_storage_bucket_iam_member" "vm_photos_rw" {
  bucket = google_storage_bucket.photos.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.gallery_vm.email}"
}

// Lets the VM write its own logs to Cloud Logging (handy for debugging the
// startup script via `journalctl` + `gcloud logging read`).
resource "google_project_iam_member" "vm_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gallery_vm.email}"
}

// ----- 6. Compute Engine VM -------------------------------------------------

locals {
  startup_script = templatefile("${path.module}/startup.sh", {
    deploy_bucket    = google_storage_bucket.deploy.name
    app_object       = google_storage_bucket_object.app_archive.name
    schema_object    = google_storage_bucket_object.schema_sql.name
    db_host          = google_sql_database_instance.mysql.private_ip_address
    db_user          = var.db_user
    db_password      = var.db_password
    db_name          = var.db_name
    gcs_photo_bucket = google_storage_bucket.photos.name
    flask_secret_key = var.flask_secret_key
  })
}

resource "google_compute_instance" "gallery" {
  name         = "${local.name}-vm"
  machine_type = var.vm_machine_type
  zone         = var.zone
  tags         = ["gallery-web"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 20
    }
  }

  network_interface {
    network    = google_compute_network.vpc.id
    subnetwork = google_compute_subnetwork.subnet.id

    // Empty access_config block = ephemeral public IP.
    access_config {}
  }

  service_account {
    email  = google_service_account.gallery_vm.email
    scopes = ["cloud-platform"]
  }

  metadata_startup_script = local.startup_script

  // The VM can't talk to Cloud SQL until the private IP exists and the user
  // is created, so make Terraform wait.
  depends_on = [
    google_sql_user.app_user,
    google_sql_database.app_db,
    google_storage_bucket_object.app_archive,
    google_storage_bucket_object.schema_sql,
    google_storage_bucket_iam_member.vm_deploy_read,
    google_storage_bucket_iam_member.vm_photos_rw,
  ]
}
