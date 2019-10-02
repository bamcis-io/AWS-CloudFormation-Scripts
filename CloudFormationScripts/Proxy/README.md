
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
9) Deploy the Squid SSM parameter in each cell, updating with the Route53 alias record name for the cache peer for each region
10) Deploy the ECR repository in each cell
11) Upload the docker image to each cell's ECR repo
12) Deploy the proxy fleet
13) Run the script to take the ENIs created for the endpoints in the cell router and add their IPs to the NLB target group