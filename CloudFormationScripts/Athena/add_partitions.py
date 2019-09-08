import sys
import boto3
from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv, [
        's3_path',
        'database',
        'table'
	]
)

source_s3_path = args["s3_path"]
db_name = args["database"]
tbl_name = args["table"]

# Removes a specified prefix
def remove_prefix(text, prefix):
    return text[text.startswith(prefix) and len(prefix):]

# Gets all s3 paths for partitions in the CloudTrail bucket
def get_cloudtrail_partitions(s3_path):
    s3_client = boto3.client("s3")
    paths = []

    if s3_path.endswith("/") == False:
        s3_path += "/"

    bucket_name = s3_path.strip("s3://").split("/")[0]
    prefix = remove_prefix(s3_path, "s3://" + bucket_name + "/")
    list_response = {}
    continuation_token = ""

    while True:  
        if continuation_token != "":
            list_response = s3_client.list_objects_v2(
                Bucket = bucket_name, 
                Delimiter = "/",
                Prefix = prefix,
                ContinuationToken = continuation_token
            )
        else:
            list_response = s3_client.list_objects_v2(
                Bucket = bucket_name,
                Prefix = prefix,
                Delimiter = "/"
            )
            
        if "CommonPrefixes" not in list_response or not list_response["CommonPrefixes"]:
            return [ s3_path ]

        for item in [x for x in list_response["CommonPrefixes"] if "CloudTrail-Digest" not in x["Prefix"]]:
            new_path = "s3://{}/{}".format(bucket_name, item["Prefix"])
            final_part = get_cloudtrail_partitions(new_path)
            paths.extend(final_part)

        if "NextContinuationToken" in list_response:
            continuation_token = list_response["NextContinuationToken"]

        if list_response["IsTruncated"] == False:
            break

    return paths

# Gets all s3 paths for partitions that currently exist in
# the specified table
def get_all_existing_partitions(DatabaseName, TableName, GlueClient):
    existing_partitions_list = []
    next_token = ""

    while True:

        if next_token != "":  
            existing_partitions = GlueClient.get_partitions(
                DatabaseName = DatabaseName,
                TableName = TableName,
                NextToken = next_token
            )
        else:
            existing_partitions = GlueClient.get_partitions(
                DatabaseName = DatabaseName,
                TableName = TableName
            )
        
        for existing in existing_partitions["Partitions"]:
            existing_partitions_list.append(existing["StorageDescriptor"]["Location"])

        if "NextToken" in existing_partitions:
                next_token = existing_partitions["NextToken"]
        else:
            break

    return set(existing_partitions_list)

print("Getting all S3 partitions in the CloudTrail S3 path.")

# Get all of the s3 paths
partitions = get_cloudtrail_partitions(source_s3_path)

glue_client = boto3.client("glue")

print("Getting table details for ", tbl_name)

# Get the table details, which we need to create new partitions
response = glue_client.get_table(
    DatabaseName = db_name,
    Name = tbl_name
)

# Inputs for the new partitions
input_format = response['Table']['StorageDescriptor']['InputFormat']
output_format = response['Table']['StorageDescriptor']['OutputFormat']
table_location = response['Table']['StorageDescriptor']['Location']
serde_info = response['Table']['StorageDescriptor']['SerdeInfo']
partition_keys = response['Table']['PartitionKeys']
columns = response['Table']['StorageDescriptor']['Columns']
parameters = response['Table']['StorageDescriptor']['Parameters']
compressed = response['Table']['StorageDescriptor']['Compressed']
top_level_params = response['Table']['Parameters']

# These will track the partitions being added in the for loop
inputs = []
counter = 0

print("Retrieving all existing partitions")

# Get the list of existing partitions
existing_partition_set = get_all_existing_partitions(
    DatabaseName = db_name, 
    TableName = tbl_name, 
    GlueClient = glue_client
)

# Don't process partitions that already exist
new_partitions_to_add = [x for x in partitions if x not in existing_partition_set]
total_new_partitions = len(new_partitions_to_add)
total_existing_partitions = len(existing_partition_set)
total_expected_partitions = total_new_partitions + total_existing_partitions

# Use a range so we can tell when we're at the end
for i in range(total_new_partitions):
    partition = new_partitions_to_add[i]
    print("Adding partition ", partition)
    end = -1

    # If the path ends in a "/", then -1 will be an empty string, so the real
    # last value will be at -2
    if partition.endswith("/"):
        end = -2

    # s3://cloudtrail/AWSLogs/123456789012/CloudTrail/ap-northeast-1/2018/05/23/
    # Format of the partition location
    path_parts = partition.split("/")

    input_dict = {
        "Values" : [
            path_parts[end - 5],    # AccountId
            path_parts[end - 4],    # CloudTrail
            path_parts[end - 3],    # Region
            path_parts[end - 2],    # Year
            path_parts[end - 1],    # Month
            path_parts[end]         # Day
        ],
        "StorageDescriptor" : {
            "Location" : partition,
            "Columns" : columns,
            "InputFormat" : input_format,
            "OutputFormat" : output_format,
            "SerdeInfo" : serde_info,
            "Parameters" : parameters,
            "Compressed" : compressed
        },
        "Parameters" : top_level_params
    }

    inputs.append(input_dict.copy())

    counter += 1

    if counter == 100 or i == total_new_partitions - 1:
        glue_client.batch_create_partition(
            DatabaseName = db_name,
            TableName = tbl_name,
            PartitionInputList = inputs
        )

        # Reset the counter and inputs
        counter = 0
        inputs = []

# Reconcile to see if we have the expected number of partitions
all_partitions = get_all_existing_partitions(
    DatabaseName = db_name, 
    TableName = tbl_name, 
    GlueClient = glue_client
)

if len(all_partitions) != total_expected_partitions:
    print("Did not add all expected partitions!")
    print("Only see ", all_partitions, " expecting ", total_expected_partitions)
else:
    print("Added ", total_new_partitions, " new partitions.")