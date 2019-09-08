import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue import DynamicFrame
from datetime import datetime
from pyspark.sql.functions import split, year, month, dayofmonth, hour, col

## @params: [JOB_NAME, file_path]
args = getResolvedOptions(sys.argv, [
		'JOB_NAME',
        'table',
        'database',
        'destination_bucket'
	]
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Data Catalog: database and table name
db_name = args['database']
tbl_name = args['table']

# S3 Output Path
output_path = "s3://" + args['destination_bucket']

# Get the source data, this grabs everything, so it could be really large
datasource0 = glueContext.create_dynamic_frame.from_catalog(
    database = db_name, 
    table_name = tbl_name, 
    transformation_ctx = "datasource0",
    additional_options = { "recurse" : True}
)

# Use this approach to read from "partitions" in the flat table
#datasource0 = glueContext.create_dynamic_frame_from_options(
#    connection_type = "s3",
#    connection_options = {
#        "paths" : [
#            source_path
#        ],
#        "recurse" : True
#    },
#    format = "json",
#    format_options = {
#        "jsonPath": "$.Records[*]"
#    },
#    transformation_ctx = "datasource0"
#)


## Resolve structs that we don't want to strings
resolve1 = datasource0.resolveChoice(
    specs = [
        ("requestParameters", "cast:string"), 
        ("responseElements", "cast:string"),
        ("additionalEventData", "cast:string"),
        ("userIdentity.sessionContext.sessionIssuer.webIdFederationData", "cast:string"),
        ("resources", "cast:string")
    ],
    transformation_ctx = "resolve1"
)

# Map and rename the data
mapping2 = resolve1.apply_mapping(
    transformation_ctx = "mapping2",
    mappings = [
        ("eventVersion", "string", "event_version", "string"),
        ("userIdentity.type", "string", "user_identity_type", "string"),
        ("userIdentity.principalId", "string", "user_identity_principal_id", "string"),
        ("userIdentity.arn", "string", "user_identity_arn", "string"),
        ("userIdentity.accountId", "string", "user_identity_account_id", "string"),
        ("userIdentity.accessKeyId", "string", "user_identity_access_key_id", "string"),
        ("userIdentity.sessionContext.attributes.mfaAuthenticated", "string", "user_identity_session_context_attributes_mfa_authenticated", "string"),
        ("userIdentity.sessionContext.attributes.creationDate", "string", "user_identity_session_context_attributes_creation_date", "timestamp"),
        ("userIdentity.sessionContext.sessionIssuer.type", "string", "user_identity_session_context_session_issuer_type", "string"),
        ("userIdentity.sessionContext.sessionIssuer.principalId", "string", "user_identity_session_context_session_issuer_principal_id", "string"),
        ("userIdentity.sessionContext.sessionIssuer.arn", "string", "user_identity_session_context_session_issuer_arn", "string"),
        ("userIdentity.sessionContext.sessionIssuer.accountId", "string", "user_identity_session_context_session_issuer_account_id", "string"),
        ("userIdentity.sessionContext.sessionIssuer.userName", "string", "user_identity_session_context_session_issuer_user_name", "string"),
        ("userIdentity.sessionContext.sessionIssuer.webIdFederationData", "string", "user_identity_session_context_session_issuer_web_id_federation_data", "string"),
        ("userIdentity.invokedBy", "string", "user_identity_invoked_by", "string"),
        ("userIdentity.userName", "string", "user_identity_user_name", "string"),
        ("eventTime", "string", "event_time", "timestamp"),
        ("eventSource", "string", "event_source", "string"),
        ("eventName", "string", "event_name", "string"),
        ("awsRegion", "string", "aws_region", "string"),
        ("sourceIPAddress", "string", "source_ip_address", "string"),
        ("userAgent", "string", "user_agent", "string"),
        ("requestID", "string", "request_id", "string"),
        ("eventID", "string", "event_id", "string"),
        ("eventType", "string", "event_type", "string"),
        ("recipientAccountId", "string", "recipient_account_id", "string"),
        ("requestParameters", "string", "request_parameters", "string"),
        ("apiVersion", "string", "api_version", "string"),
        ("responseElements", "string", "response_elements", "string"),
        ("errorCode", "string", "error_code", "string"),
        ("errorMessage", "string", "error_message", "string"),
        ("readOnly", "string", "read_only", "boolean"),
        ("vpcEndpointId", "string", "vpc_endpoint_id", "string"),
        ("additionalEventData", "string", "additional_event_data", "string"),
        ("serviceEventDetails", "string", "serivce_event_details", "string"),
        ("managementEvent", "string", "management_event", "boolean"),
        ("sharedEventId", "string", "shared_event_id", "string"),
        ("resources", "resources")
    ]
)

# Create a data frame
df = mapping2.toDF()
split_col = split(df['event_source'], '.')

# Add columns that will be used as partitions
df = df.withColumn("year", year(col("event_time"))) \
    .withColumn("month", month(col("event_time"))) \
    .withColumn("day", dayofmonth(col("event_time"))) \
    .withColumn("hour", hour(col("event_time"))) \
    .withColumn("region", col("aws_region")) \
    .withColumn("account_id", col("recipient_account_id")) \
    .withColumn("service", split(col("event_source"), '\.').getItem(0))

# Convert data frame back to dynamic frame
mapping3 = DynamicFrame.fromDF(df, glueContext, "mapping3")

# Save data to S3
datasink4 = glueContext.write_dynamic_frame.from_options(
    frame = mapping3, 
    connection_type = "s3", 
    connection_options = {
        "path": output_path,
        "partitionKeys": [
            "account_id",
            "service",
            "region",
            "year",
            "month",
            "day",
            "hour",            
        ]
    }, 
    format = "parquet", 
    transformation_ctx = "datasink4"
)

job.commit()