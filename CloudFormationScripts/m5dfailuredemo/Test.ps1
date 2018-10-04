Import-Module AWSPowerShell

Set-AWSCredential -ProfileName "mhaken-dev"

Write-S3Object -BucketName "mhaken-cf" -Key "test.template" -File "$([System.IO.Path]::GetDirectoryName($MyInvocation.InvocationName))\test.template"

New-CFNStack -StackName "m5dfailure" -Capability CAPABILITY_NAMED_IAM -Parameter @(
    @{ParameterKey = "VpcId"; ParameterValue = "vpc-0299a579"}, 
    @{ParameterKey = "KeyPairName"; ParameterValue = "mhaken-dev-us-east-1"},
    @{ParameterKey = "Subnet1"; ParameterValue = "subnet-8101c5dd"},
    @{ParameterKey = "InstanceType"; ParameterValue = "m5.large"},
	@{ParameterKey = "AdditionalVolumes"; ParameterValue = "2"}) -TemplateURL "https://s3.amazonaws.com/mhaken-cf/test.template" -DisableRollback $true