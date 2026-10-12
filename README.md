# AWS EBS IOPS Management (Terraform)

Terraform automation that monitors EBS volume metrics and raises IOPS/throughput when needed,
across multiple AWS regions. Built from three reusable modules: `iam`, `sns`, `lambda`.

## What it deploys

| Component | Region(s) | Purpose |
|-----------|-----------|---------|
| `Modify_Volume_When_Triggered` Lambda | us-east-2, us-west-2 | Adjusts EBS IOPS/throughput when a CloudWatch alarm fires |
| `Setup_CloudWatch_Alarms` Lambda | us-east-2 only | Creates/cleans alarms for instances matching the tag (default `env=k8s`) |
| EventBridge rule | us-east-2 | Runs the alarm-setup Lambda every 2 hours |
| SNS topic + email subscription | us-east-2, us-west-2 | Notifies the team when volumes are modified |
| IAM role + inline policy | global | Lambda execution permissions (`policies/lambda_policy.json`) |

## Repository layout

```
.
├── main.tf / variables.tf / outputs.tf / versions.tf
├── policies/lambda_policy.json
├── modules/
│   ├── iam/      sns/      lambda/   (lambda1.py, lambda2.py live here)
├── scripts/build-lambdas.sh      # builds the Lambda zip packages
├── terraform.tfvars.example
└── .github/                      # CI workflow + PR template
```

## Prerequisites

- Terraform >= 1.3 (CI uses 1.10.5)
- AWS CLI configured (`aws configure` or SSO) with permission to create IAM, Lambda, SNS, EventBridge
- `zip` installed (for the build script)

## Usage

```bash
git clone https://github.com/<ORG>/aws-iops-management.git
cd aws-iops-management

cp terraform.tfvars.example terraform.tfvars   # edit email_endpoint etc.
make build                                     # creates lambda1.zip / lambda2.zip
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

After apply, confirm the SNS subscription email in **each** region.

## Key variables

| Variable | Description | Default |
|----------|-------------|---------|
| `email_endpoint` | SNS alert recipient (**required**) | none |
| `project_name` | Used in resource naming | `my_IOPS_project` |
| `tag_key` / `tag_value` | Instances to monitor | `env` / `k8s` |
| `lambda_config` | Handler, runtime, timeout, memory per function | see `variables.tf` |

## Remote state (recommended for teams)

State is **not** stored in Git. Configure an S3 backend with DynamoDB locking, e.g. in a `backend.tf`:

```hcl
terraform {
  backend "s3" {
    bucket         = "<your-state-bucket>"
    key            = "aws-iops-management/terraform.tfstate"
    region         = "us-east-2"
    dynamodb_table = "<your-lock-table>"
    encrypt        = true
  }
}
```

## Contributing

1. Branch from `main`: `git checkout -b feature/<short-name>`
2. Run `make fmt validate`
3. Open a Pull Request; CI must pass and one reviewer must approve
4. Never commit `*.tfstate`, `*.tfvars`, or `.terraform/`

## Notes

- `lambda1.zip`/`lambda2.zip` are build artifacts and are git-ignored.
- The IAM policy uses broad `Resource: "*"` for several actions; tighten before production use.
