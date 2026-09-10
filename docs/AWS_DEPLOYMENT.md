# AWS deployment

This project deliberately runs the API on **ECS Fargate** and uses a managed Qdrant endpoint. That keeps the API stateless and avoids operating a stateful vector database on a single ECS task. For an all-AWS alternative, implement an `OpenSearchVectorStore` adapter behind the existing vector-store boundary.

## Prerequisites

- An AWS account, AWS CLI credentials, Terraform 1.6+, and Docker.
- A VPC with public subnets and outbound internet access. This starter assigns the task a public IP for simplicity; use private subnets plus NAT/VPC endpoints in a production network.
- A Qdrant Cloud cluster URL/API key, and two AWS Secrets Manager secrets whose **secret values are plain strings**: one OpenAI API key and one Qdrant API key.

## Deploy

From `infra/aws`:

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
terraform init
terraform apply -target=aws_ecr_repository.app
```

Build and publish the first container after Terraform creates ECR. The targeted first apply is intentional: an ECS service cannot pull an image that has not been pushed yet.

```powershell
$repo = terraform output -raw ecr_repository_url
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin ($repo -split '/')[0]
docker build -t knowledgeops:0.1.0 ../..
docker tag knowledgeops:0.1.0 "${repo}:0.1.0"
docker push "${repo}:0.1.0"
terraform apply -var 'image_tag=0.1.0'
```

Terraform outputs the load balancer URL. Check `/healthz`, seed a document, and then run `python evals/run_evals.py --base-url <ALB_URL>`.

## Cost and security notes

- Fargate, ALB, logs, ECR storage, Secrets Manager, Qdrant Cloud, and OpenAI usage can all incur cost. Tear down the demo with `terraform destroy` when finished.
- The Terraform example exposes port 80 on the ALB. Put CloudFront/WAF, HTTPS/ACM, authentication, private task subnets, and least-privilege IAM in front of a public deployment.
- The task execution role has read access only to the two supplied secret ARNs, while the application receives only the secret values as environment variables.
