.PHONY: build fmt validate plan apply

build:      ## Package Lambda functions
	./scripts/build-lambdas.sh

fmt:        ## Format Terraform code
	terraform fmt -recursive

validate:   ## Static validation (no AWS access needed)
	terraform init -backend=false
	terraform validate

plan: build ## Preview changes
	terraform init
	terraform plan -out=tfplan

apply:      ## Apply the reviewed plan
	terraform apply tfplan
