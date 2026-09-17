variable "aws_region" {
  description = "AWS region for the LIVLINK demo environment."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Prefix used for AWS resource names."
  type        = string
  default     = "livlink"
}

variable "instance_type" {
  description = "EC2 size. t3.small is the minimum recommended size for API, frontend build and PostgreSQL on one demo host."
  type        = string
  default     = "t3.small"
}

variable "app_repository_url" {
  description = "HTTPS Git URL that the EC2 instance can clone. It must be publicly readable or use a separate approved private-repository delivery method."
  type        = string
  default     = "https://github.com/HirushaSipsara/Code_Fest_Designathon_Team_Waffles.git"
}

variable "app_repository_ref" {
  description = "Git branch or tag deployed by the EC2 bootstrap."
  type        = string
  default     = "main"
}

variable "postgres_password" {
  description = "Strong database password for the demo PostgreSQL container. Supply through TF_VAR_postgres_password; never commit it."
  type        = string
  sensitive   = true
}

variable "http_ingress_cidr" {
  description = "CIDR allowed to reach the HTTP demo endpoint. Keep 0.0.0.0/0 only while a public demo is required."
  type        = string
  default     = "0.0.0.0/0"
}

variable "tags" {
  description = "Additional AWS tags."
  type        = map(string)
  default     = {}
}
