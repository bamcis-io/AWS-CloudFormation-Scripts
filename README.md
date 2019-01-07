# BAMCIS CloudFormation Scripts

A collection of useful CloudFormation scripts for automating deployment as well as entire solutions deployed
directly from CloudFormation.

## Table of Contents
- [Usage](#usage)
  * [Networking](#networking)
  * [Directory Service](#directory-service)
  * [CloudEndure](#cloudendure)
  * [DDNS](#ddns)
  * [Athena](#athena-demo)
  * [Active Directory](#active-directory)
  * [VPC Endpoints](#vpc-endpoints)

## Usage

### Networking
Easily deploys a VPC with public and private subnets in 3 AZs. Includes optional IPv6 support as well as enabling DNS support.

### Directory Service
Deploys a new AWS Microsoft AD Directory Service.

### CloudEndure
Deploys the networking and IAM infrastructure to start using CloudEndure replication.

### DDNS
A complete solution for DDNS clients that use Route53 for DNS. This provides an "authenticated" (kind of) endpoint for clients.

### Athena Demo
A cross account Athena query demo.

### Active Directory
A working project on deploying a new Active Directory forest, not quite ready yet.

### VPC Endpoints
Deploy VPC Interface and Gateway Endpoints inside a VPC. There is also a wrapper CF stack that deploys a dedicated VPC environment to host the PrivateLink and Gateway endpoints as well as Route53 Resolver endpoints for a complete private access solution.