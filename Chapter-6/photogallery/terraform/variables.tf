variable "project_id" {
  description = "GCP project ID that owns all resources."
  type        = string

  validation {
    condition     = length(var.project_id) >= 6 && length(var.project_id) <= 30
    error_message = "project_id must be 6-30 characters (GCP project ID rules)."
  }
}

variable "region" {
  description = "Region for the subnet, Cloud SQL, and GCS buckets."
  type        = string
  default     = "us-central1"

  validation {
    condition     = contains(["us-central1", "us-east1", "us-east4", "us-west1"], var.region)
    error_message = "region must be one of: us-central1, us-east1, us-east4, us-west1."
  }
}

variable "zone" {
  description = "Zone for the Compute Engine VM. Must live inside var.region."
  type        = string
  default     = "us-central1-a"
}

variable "name_prefix" {
  description = "Prefix applied to every resource name so re-runs / classmates don't collide."
  type        = string
  default     = "photogallery"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,20}$", var.name_prefix))
    error_message = "name_prefix must be lowercase alphanumeric/dash, 3-21 chars, start with a letter."
  }
}

// --- Networking ---

variable "subnet_cidr" {
  description = "CIDR for the custom VPC subnet (assignment requires a /16 from 10.0.0.0/16)."
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrnetmask(var.subnet_cidr))
    error_message = "subnet_cidr must be a valid CIDR block."
  }
}

variable "ssh_source_ranges" {
  description = "CIDR ranges allowed to SSH (port 22) into the VM. Default is open; tighten to your /32 for grading."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

// --- Database ---

variable "db_tier" {
  description = "Cloud SQL machine tier. Assignment requires db-n1-standard-1."
  type        = string
  default     = "db-n1-standard-1"
}

variable "db_name" {
  description = "Logical database name created inside the Cloud SQL instance."
  type        = string
  default     = "photogallerydb"
}

variable "db_user" {
  description = "Application DB user (granted full access to var.db_name)."
  type        = string
  default     = "photogallery"
}

variable "db_password" {
  description = "Password for the application DB user. Set via terraform.tfvars or TF_VAR_db_password."
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 12
    error_message = "db_password must be at least 12 characters."
  }
}

// --- Application ---

variable "vm_machine_type" {
  description = "Compute Engine machine type. Assignment requires e2-standard-2."
  type        = string
  default     = "e2-standard-2"
}

variable "flask_secret_key" {
  description = "Flask session secret. Set via terraform.tfvars or TF_VAR_flask_secret_key."
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.flask_secret_key) >= 16
    error_message = "flask_secret_key must be at least 16 characters."
  }
}

variable "app_source_dir" {
  description = "Path to the Flask app source that gets packaged onto the VM. Default resolves to the parent photogallery/ directory regardless of where terraform is invoked from."
  type        = string
  default     = ""
}
