variable "ami_id" {
  description = "Festgelegtes Amazon-Linux-2023-x86_64-Image in der Zielregion; bestehende Instanz beibehalten."
  type        = string
  validation {
    condition     = can(regex("^ami-[0-9a-f]{8}([0-9a-f]{9})?$", var.ami_id))
    error_message = "Eine gueltige, explizite AMI-ID ist erforderlich."
  }
}

variable "web_allowed_cidrs" {
  description = "IPv4-Netze fuer die Web-Konsole."
  type        = list(string)
  default     = ["0.0.0.0/0"]
  validation {
    condition     = alltrue([for cidr in var.web_allowed_cidrs : can(cidrnetmask(cidr))])
    error_message = "Gueltige IPv4-CIDRs erforderlich."
  }
}

variable "aws_region" {
  description = "Im Learner Lab freigegebene AWS-Region."
  type        = string
  default     = "eu-central-1"
}

variable "instance_type" {
  description = "Kleiner x86_64-Instanztyp des Learner Labs."
  type        = string
  default     = "t2.micro"
  validation {
    condition     = contains(["t2.micro", "t3.micro"], var.instance_type)
    error_message = "Bitte t2.micro oder t3.micro verwenden."
  }
}

variable "instance_name" {
  description = "Name der Instanz und Praefix fuer Key Pair und Security Group."
  type        = string
  default     = "tictactest-dev"
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9-]{0,49}$", var.instance_name))
    error_message = "Name: 1 bis 50 Buchstaben, Ziffern oder Bindestriche; mit Buchstabe beginnen."
  }
}

variable "ssh_public_key_path" {
  description = "Lokaler Pfad zum oeffentlichen OpenSSH-Schluessel, niemals zum privaten."
  type        = string
  default     = "~/.ssh/tictactest_ed25519.pub"
  validation {
    condition     = can(regex("^ssh-(ed25519|rsa) ", trimspace(file(pathexpand(var.ssh_public_key_path)))))
    error_message = "Der Pfad muss auf einen vorhandenen oeffentlichen Ed25519- oder RSA-OpenSSH-Schluessel zeigen."
  }
}

variable "allowed_ssh_cidr" {
  description = "Vertrauenswuerdige oeffentliche IPv4-Adresse mit /32; kein offenes SSH."
  type        = string
  validation {
    condition     = can(cidrnetmask(var.allowed_ssh_cidr)) && can(regex("/32$", var.allowed_ssh_cidr))
    error_message = "Eine gueltige einzelne IPv4-Adresse mit /32 ist erforderlich."
  }
}

variable "environment" {
  description = "Umgebung fuer AWS-Tags; noch keine getrennten Deployments."
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Erlaubt sind dev, staging und prod."
  }
}

variable "subnet_id" {
  description = "Optionales vorhandenes oeffentliches Subnetz; null sucht ein Default-Subnetz."
  type        = string
  default     = null
  nullable    = true
}
