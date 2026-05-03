// Remote state in a GCS bucket. The bucket itself is created out-of-band
// (see README "Bootstrap" section) because Terraform cannot create the
// bucket that holds its own state on the first run.
//
// Override `bucket` at init time if your bucket name differs:
//   terraform init -backend-config="bucket=<your-tfstate-bucket>"

terraform {
  backend "gcs" {
    bucket = "se4220-final-jp-260502-tfstate"
    prefix = "photogallery/state"
  }
}
