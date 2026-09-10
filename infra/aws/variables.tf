variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "project_name" {
  type    = string
  default = "knowledgeops"
}

variable "image_tag" {
  type    = string
  default = "0.1.0"
}

variable "vpc_id" {
  type        = string
  description = "VPC containing the ALB and ECS tasks."
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "At least two public subnet IDs in different availability zones."
}

variable "openai_api_key_secret_arn" {
  type        = string
  sensitive   = true
  description = "Secrets Manager ARN containing only the OpenAI API key as its secret string."
}

variable "qdrant_api_key_secret_arn" {
  type        = string
  sensitive   = true
  description = "Secrets Manager ARN containing only the Qdrant API key as its secret string."
}

variable "qdrant_url" {
  type        = string
  description = "Qdrant Cloud HTTPS endpoint."
}

variable "chat_model" {
  type    = string
  default = "gpt-4.1-mini"
}

variable "embedding_model" {
  type    = string
  default = "text-embedding-3-small"
}

