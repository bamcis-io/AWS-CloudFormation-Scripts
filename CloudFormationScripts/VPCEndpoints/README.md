# AWS VPC Endpoints
There are 3 main templates, one that deploys the ENI based endpoints (Interface Endpoints), one that deploys the Gateway based Endpoints, and one that wraps both of those templates as well as the private networking template. This third template provides a centralized, private VPC that can be used to private access to supported AWS APIs over PrivateLink. 

## Route53 Resolver

If you plan to use the dedicated-endpoint-vpc, you may also want to use the route53-resolver-on-premises-forwarding template. This will create a rule that will ensure supported AWS services that have PrivateLink endpoints are resolved internally while forwarding all other DNS requests to your specified DNS server. This allows you to take advantage of PrivateLink endpoints while still controlling DNS resolution and proxying for all other services that are not supported.

## Deployment
The `deploy.ps1` PowerShell script will deploy the `dedicated-endpoint-vpc.template` CloudFormation stack with all child templates. The script uploads all of the required templates to an S3 bucket and then executes the parent stack. 

The pertinent variable parameters you may want to define are at the beginning of the script:

    # Update these values with your own
    $ProfileName = "mhaken-dev"
    $Bucket = "mhaken-cf"
    $Organization = "bamcis.io"
    $Environment = "dev"
    $OnPremDNS1 = "172.31.3.4"
    $OnPremDNS2 = ""
