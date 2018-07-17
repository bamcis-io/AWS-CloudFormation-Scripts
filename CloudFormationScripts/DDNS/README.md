# Dynamic DNS Endpoint

## Usage
This CloudFormation template creates an API Gateway endpoint that accepts requests from a client and updates a record in a record set in Route53. The only parameter is the `HostedZoneId` of the zone
that will receive updates from DDNS clients.

The client sends a GET request to the endpoint including the Route53 hosted zone id, domain, and record name (i.e. A record) with an optional `ttl` query string parameter. A request may look like (where 
`${ApiGateway}` is a placeholder for the function's actual id):

    GET https://${ApiGateway}.execute-api.us-east-1.amazonaws.com/ddns/Z1UJRXOUMOOFQ8/bamcis.io/myhost?ttl=120"

This request is then parsed in API Gateway to extract the Hosted Zone Id, the Domain, and the Record Name. Additionally, since this request includes the `ttl` query string, it is also extracted. These
variables are injected into an XML template. The API itself is setup with a backend of AWS Service integration. The intregated service is Route53. This means we're using the credentials of API Gateway
as frontend to send requests into the Route53 API. Each request must have an ApiKey included in the header which is the means of securing this endpoint, so the API key must be treated like a set of
credentials on the client. The header in the request is:

     x-api-key:{api_key}

And that's all there is to using it. This means no IAM credentials or permissions are needed on potentially untrusted devices. The worst someone could do is update the DNS records for clients in the hosted
zone, so make sure to only use this zone for those purposes.
