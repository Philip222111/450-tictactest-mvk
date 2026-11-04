provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "TicTacTest"
      Environment = var.environment
      ManagedBy   = "OpenTofu"
    }
  }
}
