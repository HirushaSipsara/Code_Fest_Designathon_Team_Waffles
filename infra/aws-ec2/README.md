# LIVLINK AWS EC2 demo deployment

This Terraform configuration creates one Ubuntu EC2 instance running the full
LIVLINK demo as Docker containers:

`Internet → Nginx frontend → FastAPI backend → PostgreSQL`

The only public service is HTTP on port 80. SSH is intentionally not opened;
use AWS Systems Manager Session Manager for administration. This is a
hackathon-demo architecture, not a production HA deployment. PostgreSQL runs
on the same instance and the public endpoint is HTTP only.

## Before applying

1. Install and authenticate the AWS CLI: `aws configure` or an approved IAM/SSO profile.
2. Confirm the account and intended region: `aws sts get-caller-identity --region ap-south-1`.
3. Commit and push the application source, including `docker-compose.prod.yml`, Dockerfiles and this `infra` directory.
4. Ensure `app_repository_url` is publicly cloneable from EC2. A private repository needs an approved private delivery mechanism; do not put a GitHub personal token in Terraform files or user data.
5. Create a local `terraform.tfvars` from `terraform.tfvars.example`, using a unique database password. Never commit it.

The frontend currently has no `package-lock.json`, so its demo container uses
`npm install`. Generate and commit a lockfile before treating the deployment as
a reproducible production release.

## Deploy

```powershell
cd infra/aws-ec2
terraform init
terraform fmt -check -recursive
terraform validate
terraform plan -out livlink-demo.tfplan
terraform apply livlink-demo.tfplan
```

After completion, use `terraform output -raw public_url`. Initial boot takes a
few minutes because the EC2 host installs Docker, clones the repository and
builds the frontend and backend images.

## Verify and operate

```powershell
terraform output
aws ssm start-session --target <instance-id> --region ap-south-1
# On the EC2 host:
cd /opt/livlink
docker compose -f docker-compose.prod.yml --env-file .env.deploy ps
curl http://localhost/api/health
```

## Cost and teardown

`t3.small`, a 20 GiB gp3 volume and public IPv4 can incur AWS charges. Destroy
the demo as soon as judging is complete:

```powershell
terraform destroy
```

Destroying the instance also removes the locally hosted PostgreSQL data.
