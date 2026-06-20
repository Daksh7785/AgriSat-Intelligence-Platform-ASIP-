variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "agrisense-ai-platform"
}

variable "region" {
  description = "GCP Region to deploy resources"
  type        = string
  default     = "asia-south1" # Mumbai, India (for data residency compliance)
}
