data "aws_iam_instance_profile" "lab" {
  name = "LabInstanceProfile"
}

resource "aws_eip" "web" {
  domain = "vpc"
  tags   = { Name = "${var.instance_name}-web" }
}

resource "aws_eip_association" "web" {
  instance_id   = aws_instance.app.id
  allocation_id = aws_eip.web.id
}

# Bucket creation is a bootstrap step: the lab explicitly denies the provider's
# GetBucketObjectLockConfiguration read. Retain the bucket across stack rebuilds.
variable "artifact_bucket" {
  type        = string
  description = "Existing private artifact bucket, created once with a unique name."
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = var.artifact_bucket
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = var.artifact_bucket
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = var.artifact_bucket
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

locals {
  runtime_files = {
    "tictactest.service" = "/etc/systemd/system/tictactest.service"
    "nginx.conf"         = "/etc/nginx/conf.d/tictactest.conf"
    "deploy_release.py"  = "/usr/local/lib/tictactest/deploy_release.py"
    "provision.sh"       = "/usr/local/lib/tictactest/provision.sh"
  }
  bootstrap = join("\n", concat([
    "#!/usr/bin/env bash", "set -euo pipefail",
    "mkdir -p /usr/local/lib/tictactest /etc/nginx/conf.d",
    ], [for source, target in local.runtime_files :
    "echo '${base64encode(file("${path.module}/runtime/${source}"))}' | base64 -d > '${target}'"
  ], ["BACKEND_ORIGIN='' bash /usr/local/lib/tictactest/provision.sh"]))
}

# Also applies runtime updates to the existing instance; user_data is first-boot only.
resource "aws_ssm_document" "runtime" {
  name          = "${var.instance_name}-runtime"
  document_type = "Command"
  content = jsonencode({
    schemaVersion = "2.2"
    mainSteps     = [{ action = "aws:runShellScript", name = "runtime", inputs = { runCommand = [local.bootstrap] } }]
  })
}

resource "aws_ssm_association" "runtime" {
  name             = aws_ssm_document.runtime.name
  document_version = aws_ssm_document.runtime.latest_version
  targets {
    key    = "InstanceIds"
    values = [aws_instance.app.id]
  }
  wait_for_success_timeout_seconds = 300
  depends_on                       = [aws_eip_association.web]
}
