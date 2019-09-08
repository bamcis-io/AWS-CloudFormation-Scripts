import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue import DynamicFrame
from datetime import datetime, timedelta
from pyspark.sql.functions import split, year, month, dayofmonth, hour, col

## @params: [JOB_NAME, file_path]
args = getResolvedOptions(sys.argv, [
		'JOB_NAME',
        's3_bucket',
        'destination_bucket',
		'days_ago'
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
days_ago = int(args['days_ago']) # Defaults to 7

# S3 bucket path, like s3://bucket/AWSLogs/
s3_bucket = args['s3_bucket']

now = datetime.now()
date_in_past = now - timedelta(days = days_ago)

# We're going to back 1 day and ensure we're not missing data, job bookmarks will ensure we
# don't reprocess and existing file
# Using day = 01, we know going back 1 day will take us to the previous month
current_year = str(date_in_past.year)
current_month = str(date_in_past.month).zfill(2)
current_day = str(date_in_past.day).zfill(2)

# S3 Output Path
output_path = "s3://" + args['destination_bucket']

# Get everything that is newer than the specified date, job bookmarks will ensure
# we don't duplicate data
pushdown = "to_date(concat(year, '-', month, '-', day)) >= to_date(concat({}, '-', {}, '-', {}))".format(current_year, current_month, current_day)

# Get the source data using the pushdown to only grab certain partitions
datasource0 = glueContext.create_dynamic_frame.from_catalog(
    database = db_name, 
    table_name = tbl_name, 
    transformation_ctx = "datasource0",
    additional_options = { "recurse" : True},
	push_down_predicate = pushdown
)

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
        ("resources", "resources"),
        ("year", "string", "year", "integer"),
        ("month", "string", "month", "integer"),
        ("day", "string", "day", "integer"),
        ("hour", "string", "hour", "integer"),
        ("accountid", "account_id"),
        ("region", "region")
    ]
)

# Create a data frame
df = mapping2.toDF()
split_col = split(df['event_source'], '.')

# Add columns that will be used as partitions
df = df.withColumn("service", split(col("event_source"), '\.').getItem(0))

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