## Build the docker image
1) Run the build.ps1 script to build the docker image

## Deploy the regional proxy cell router and cells
1) Deploy regional cell router private networking
2) Deploy cell router
3) Deploy regional cell public networking, 2 to n (use public so it can proxy for AWS services that don't have endpoints)
4) Deploy desired endpoints to the public VPC in each cell
5) Deploy ECS default account attributes in each cell
6) Deploy the Squid SSM parameter in each cell
7) Deploy the ECR repository in each cell
8) Upload the docker image to each cell's ECR repo
9) Deploy the proxy fleet in each cell using the CellRouter IAM Role as input
10) Create PrivateLink endpoints in the cell router for each cell
11) Run the script to take the ENIs created for the endpoints in the cell router and add their IPs to the NLB target group

## Deploy the local proxy cell router and cells
1) Deploy the cell router private networking
2) Deploy the cell router
3) Create PrivateLink endpoints in the cell router for each cell
4) Deploy the local cells, create a public VPC in the local region and a private VPC in each additional region that requires access
5) Create a peering connection between the private VPCs and the public VPC
6) Update the route tables in each VPC with the cidr blocks of the peer
7) Create a Route53 private hosted zone in the public VPC
8) Create a PrivateLink endpoint to the cell router in the same region from each private VPC in each cell (this will also create the Route53 alias record)
9) Manually approve the Endpoint service requests in each regional cell router account
10) Deploy the Squid SSM parameter in each cell, make sure to include a peer statement for each region you want to forward to
11) Deploy the ECR repository in each cell
12) Upload the docker image to each cell's ECR repo
13) Deploy the proxy fleet
14) Run the script to take the ENIs created for the endpoints in the cell router and add their IPs to the NLB target group

## Deploy the proxy to a customer VPC
1) Add an endpoint to the cell router service in the customer VPC, making sure to use the same region as the VPC for the right local proxy cell router
2) Manually approve the endpoint service connection in the cell router account
3) Update the instances in the VPC and set both the HTTPS_PROXY and HTTP_PROXY environment variables to the VPC endpoint DNS name, set NO_PROXY=169.254.169.254