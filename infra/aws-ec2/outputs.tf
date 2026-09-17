output "public_url" {
  description = "Public HTTP URL for the LIVLINK demo. Add HTTPS through a load balancer/domain before production use."
  value       = "http://${aws_instance.app.public_ip}"
}

output "instance_id" {
  description = "EC2 instance ID for AWS Systems Manager Session Manager."
  value       = aws_instance.app.id
}

output "ssm_start_session" {
  description = "Run this locally to access the host without opening SSH."
  value       = "aws ssm start-session --target ${aws_instance.app.id} --region ${var.aws_region}"
}
