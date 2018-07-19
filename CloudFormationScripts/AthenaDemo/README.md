# Athena Cross Account Query Demo

This set of CloudFormation scripts demonstrates the ability of using Athena to query data in an S3 bucket that belongs to a different account.

## Table of Contents
- [Instructions](#instructions)
- [Security Considerations](#security-considerations)

## Instructions

1) Decide on an S3 Bucket name that will be used. This bucket name will be an input to both CloudFormation scripts that will be run.

2) Deploy the `athena-demo.template` into Account A, supplying the bucket name you decided on adbove. Take note of the `RoleArn` output.
   1) This script creates an IAM Role, `AthenaUserRole`, that users will assume in order to access the remote S3 Bucket
   2) An IAM policy associated with that role that allows full access to `S3`, `Athena`, and `Glue`. You may want to tailor this policy to your needs. 
   3) An IAM group and IAM Policy attached to that group are also created that grant members of the group permissions to assume the `AthenaUserRole` IAM Role
   4) An AWS Glue database that will contain saved Athena queries and the demo database table.
   5) Three Athena Named/Saved Queries. One query demonstrates creating a database/schema (but isn't necessary to run since it was created in the previous step), one demonstrates creating a table that is stored in the AWS Glue Data Catalog, and the last previews the contents of the table.

3) Deploy the `caa-bucket.template` into Account B, supplying the `RoleArn` value from the other CF script and the bucket name you decided on in step **1**. 
   1) This script creates the bucket that will contain the demo "data lake" file(s).
   2) The script also assigns a bucket policy that grants the provided IAM Role Arn with the required permissions to run Athena queries.

4) Once that CF script is complete, upload 1 to all of the included CSV files to the bucket that was created. 

5) If your IAM user account in Account A does not have full admin access, or you want to create a test user with limited privileges, setup that user and add them to the IAM Group, `AthenaUsersGroup`, that was created in Account A. 

6) After the CF scripts have been run and the files have been uploaded to S3, go to the Management Console in Account A. Use the `Switch Role` function in the UI or copy and paste the link from the `SwitchRoleUrl` output of the first CF script from step **2**. 

7) You've now assumed a role in Account A. This single specific role has been authorized permissions on the S3 Bucket in Account B. This means that you don't have to maintain an extensive list of users in the remote side S3 Bucket Policy and all updates to that access is based on what users you allow to assume the role on Account A. 

8) A Glue database has been created with the CF script solely for the purposes of needing a database to associate the saved named queries with.

9) Go to the Athena service page. Three Saved Queries were created, you will need to run 2 of them. 
   1) The first is `Demo Db Create` which is an example of how to create a Glue database/schema. However, since the Glue database already exists, you don't need to run this, it's just an example if you were to generate all of your DDL statements separately. 
   2) The next Saved Query is `Demo Table Create`. While using the assumed IAM Role, run this query (make sure you've seleced the correct database to run this against, it should auto-populate). If successful, a new has been created. 
   3) Lastly, select the third Saved Query, `Demo Table Preview` and run it. You should get back 10 rows of data from the remote S3 bucket.

### Conclusion

That's it, you've now successfully set up a design pattern to use Athena to query data in S3 Buckets in a cross account access pattern without needing to maintain extensive, complex, and not easily maintainable user authorizations in an S3 Bucket Policy (in account that you may not even control). 

## Security Considerations

You may want to add conditions to the `AssumeRolePolicyDocument` on the `AthenaUserRole` IAM Role, for example, to enforce MFA logon, add the following:

    "Condition": { 
	    "Bool": { 
		    "aws:MultiFactorAuthPresent": true 
	    } 
	}

Since all of the access to the remote bucket now appears to come from one IAM role, this approach does make it harder for attribution to individual users for audit purposes. However, all calls to the STS AssumeRole API in Account A are logged with the user that performed the action. In Account B you can enable S3 Server Access Logs and those logs will show you the temporary credential information that includes the original user name. This is a snippet from one of the server access log files, it is the **Requestor** field. 

    arn:aws:sts::123456789012:assumed-role/AthenaUserRole/myusername

This field shows the IAM Role that was used to access the S3 object along with the RoleSessionName, i.e. `myusername`. In a standard AssumeRole call, the RoleSessionName is the IAM user name. The RoleSessionName is also logged in the AssumeRole API call in Account A, so even if the user uses a non-standard RoleSessionName, you can still correlate the S3 Server Access Log requestor field back to the user that made the AssumeRole API call.