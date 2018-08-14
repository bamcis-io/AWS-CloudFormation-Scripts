# AWS VPC Networking
The included template deploys a VPC across 2 or 3 availability zones, including a public and private subnet in each AZ. An Internet Gateway (IGW) is deployed for the VPC and a NAT Gateway is deployed per AZ. All necessary routes and route tables are deployed. You may specify whether EC2 instances are provided public DNS host names.

IPv6 can optionally be enabled, which also includes deploying an egress only gateway. 

3 default Security Groups are also created, one for a Bastion Host to allow remote access, one for SSH management of internal EC2 instances from the Bastion Host, and one for Windows Remote Management of internal EC2 instances from the Bastion Host.


