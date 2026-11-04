output "web_url" {
  value = "http://${aws_eip.web.public_dns}"
}

output "security_group_id" {
  value = aws_security_group.ssh.id
}

output "instance_id" {
  description = "ID der EC2-Instanz."
  value       = aws_instance.app.id
}

output "public_ipv4" {
  description = "Oeffentliche IPv4-Adresse (kann sich nach Stop/Start aendern)."
  value       = aws_eip.web.public_ip
}

output "public_dns" {
  description = "Oeffentlicher DNS-Name, sofern im vorhandenen VPC aktiviert."
  value       = aws_eip.web.public_dns
}

output "ssh_command" {
  description = "Standard-Schluesselpfad; bei anderem privaten Schluessel anpassen."
  value       = "ssh -i ~/.ssh/tictactest_ed25519 ec2-user@${aws_eip.web.public_dns}"
}

output "console_url" { value = "http://${aws_eip.web.public_dns}/terminal/" }
output "backend_version_url" { value = "http://${aws_eip.web.public_dns}/backend-version.json" }
output "frontend_version_url" { value = "http://${aws_eip.web.public_dns}/version.json" }
output "artifact_bucket" { value = var.artifact_bucket }
