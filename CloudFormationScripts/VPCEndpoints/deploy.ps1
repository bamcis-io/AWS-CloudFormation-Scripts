Import-Module AWSPowerShell

# Update these values with your own
$ProfileName = "mhaken-dev"
$Bucket = "mhaken-cf"
$Organization = "bamcis.io"
$Environment = "dev"
$OnPremDNS1 = "172.31.3.4"
$OnPremDNS2 = ""

Set-AWSCredential -ProfileName $ProfileName

# The file paths for the -File parameter only work this way if you execute this script using the "Networking" folder as your present working directory

Write-S3Object -BucketName $Bucket -Key "dedicated-endpoint-vpc.template" -File "$([System.IO.Path]::GetDirectoryName($MyInvocation.InvocationName))\dedicated-endpoint-vpc.template"
Write-S3Object -BucketName $Bucket -Key "gateway-endpoints.template" -File "$([System.IO.Path]::GetDirectoryName($MyInvocation.InvocationName))\gateway-endpoints.template"
Write-S3Object -BucketName $Bucket -Key "interface-endpoints.template" -File "$([System.IO.Path]::GetDirectoryName($MyInvocation.InvocationName))\interface-endpoints.template"
Write-S3Object -BucketName $Bucket -Key "networking-private-vpc-3-az.template" -File "$([System.IO.Directory]::GetParent([System.IO.Path]::GetDirectoryName($MyInvocation.InvocationName)))\Networking\networking-private-vpc-3-az.template"
Write-S3Object -BucketName $Bucket -Key "route53-resolver-endpoints.template" -File "$([System.IO.Directory]::GetParent([System.IO.Path]::GetDirectoryName($MyInvocation.InvocationName)))\Networking\route53-resolver-endpoints.template"
Write-S3Object -BucketName $Bucket -Key "route53-resolver-on-premises-forwarding.template" -File "$([System.IO.Path]::GetDirectoryName($MyInvocation.InvocationName))\route53-resolver-on-premises-forwarding.template"


New-CFNStack -StackName "vpc-endpoints" -Capability CAPABILITY_NAMED_IAM -Parameter @(
    # Stack template URLs
	@{ParameterKey = "NetworkingStackUrl"; ParameterValue = "https://s3.amazonaws.com/$Bucket/networking-private-vpc-3-az.template"}, 
    @{ParameterKey = "InterfaceEndpointsStackUrl"; ParameterValue = "https://s3.amazonaws.com/$Bucket/interface-endpoints.template"}, 
    @{ParameterKey = "GatewayEndpointsStackUrl"; ParameterValue = "https://s3.amazonaws.com/$Bucket/gateway-endpoints.template"}, 
    @{ParameterKey = "Route53ResolverEndpointsStackUrl"; ParameterValue = "https://s3.amazonaws.com/$Bucket/route53-resolver-endpoints.template"}, 
	@{ParameterKey = "Route53ResolverForwardingRuleStackUrl"; ParameterValue = "https://s3.amazonaws.com/$Bucket/route53-resolver-on-premises-forwarding.template"},
	
	# Route53 Resolver Rule Parameters
	@{ParameterKey = "OnPremisesDNSServerIpAddress"; ParameterValue = $OnPremDNS1}, 
	@{ParameterKey = "BackupOnPremisesDNSServerIpAddress"; ParameterValue = $OnPremDNS2}, 

	# Networking Parameters
    @{ParameterKey = "VpcCidrBlock"; ParameterValue = "192.168.252.0/22"},
    @{ParameterKey = "AZ1PrivateSubnet1CidrBlock"; ParameterValue = "192.168.252.0/24"},
    @{ParameterKey = "AZ2PrivateSubnet1CidrBlock"; ParameterValue = "192.168.253.0/24"},
    @{ParameterKey = "AZ3PrivateSubnet1CidrBlock"; ParameterValue = "192.168.254.0/24"},
    @{ParameterKey = "AvailabilityZone1"; ParameterValue = "us-east-1a"},
    @{ParameterKey = "AvailabilityZone2"; ParameterValue = "us-east-1b"},
    @{ParameterKey = "AvailabilityZone3"; ParameterValue = "us-east-1d"},
    @{ParameterKey = "EnablePublicDnsHostNames"; ParameterValue = "true"},
    @{ParameterKey = "EnableDnsSupport"; ParameterValue = "true"},

	# Route53 Endpoint Parameters
    @{ParameterKey = "Subnet1DNSInboundIPAddress"; ParameterValue = "192.168.252.53"},
    @{ParameterKey = "Subnet2DNSInboundIPAddress"; ParameterValue = "192.168.253.53"},
    @{ParameterKey = "Subnet3DNSInboundIPAddress"; ParameterValue = "192.168.254.53"},

	# Common Parameters
    @{ParameterKey = "OrganizationTag"; ParameterValue = $Organization},
    @{ParameterKey = "ApplicationTag"; ParameterValue = "centralized-vpce"},
    @{ParameterKey = "EnvironmentTag"; ParameterValue = $Environment}) -TemplateURL "https://s3.amazonaws.com/$Bucket/dedicated-endpoint-vpc.template"


<#
Update-CFNStack -StackName "vpc-endpoints" -Capability CAPABILITY_NAMED_IAM -Parameter @(
    # Stack template URLs
	@{ParameterKey = "NetworkingStackUrl"; ParameterValue = "https://s3.amazonaws.com/$Bucket/networking-private-vpc-3-az.template"}, 
    @{ParameterKey = "InterfaceEndpointsStackUrl"; ParameterValue = "https://s3.amazonaws.com/$Bucket/interface-endpoints.template"}, 
    @{ParameterKey = "GatewayEndpointsStackUrl"; ParameterValue = "https://s3.amazonaws.com/$Bucket/gateway-endpoints.template"}, 
    @{ParameterKey = "Route53ResolverEndpointsStackUrl"; ParameterValue = "https://s3.amazonaws.com/$Bucket/route53-resolver-endpoints.template"}, 
	@{ParameterKey = "Route53ResolverForwardingRuleStackUrl"; ParameterValue = "https://s3.amazonaws.com/$Bucket/route53-resolver-on-premises-forwarding.template"}, 
	
	# Route53 Resolver Rule Parameters
	@{ParameterKey = "OnPremisesDNSServerIpAddress"; ParameterValue = "172.31.3.4"}, 
	@{ParameterKey = "BackupOnPremisesDNSServerIpAddress"; ParameterValue = ""}, 

	# Networking Parameters
    @{ParameterKey = "VpcCidrBlock"; ParameterValue = "192.168.252.0/22"},
    @{ParameterKey = "AZ1PrivateSubnet1CidrBlock"; ParameterValue = "192.168.252.0/24"},
    @{ParameterKey = "AZ2PrivateSubnet1CidrBlock"; ParameterValue = "192.168.253.0/24"},
    @{ParameterKey = "AZ3PrivateSubnet1CidrBlock"; ParameterValue = "192.168.254.0/24"},
    @{ParameterKey = "AvailabilityZone1"; ParameterValue = "us-east-1a"},
    @{ParameterKey = "AvailabilityZone2"; ParameterValue = "us-east-1b"},
    @{ParameterKey = "AvailabilityZone3"; ParameterValue = "us-east-1d"},
    @{ParameterKey = "EnablePublicDnsHostNames"; ParameterValue = "true"},
    @{ParameterKey = "EnableDnsSupport"; ParameterValue = "true"},

	# Route53 Endpoint Parameters
    @{ParameterKey = "Subnet1DNSInboundIPAddress"; ParameterValue = "192.168.252.53"},
    @{ParameterKey = "Subnet2DNSInboundIPAddress"; ParameterValue = "192.168.253.53"},
    @{ParameterKey = "Subnet3DNSInboundIPAddress"; ParameterValue = "192.168.254.53"},

	# Common Parameters
    @{ParameterKey = "OrganizationTag"; ParameterValue = $Organization},
    @{ParameterKey = "ApplicationTag"; ParameterValue = "centralized-vpce"},
    @{ParameterKey = "EnvironmentTag"; ParameterValue = $Environment}) -TemplateURL "https://s3.amazonaws.com/$Bucket/dedicated-endpoint-vpc.template"
#>