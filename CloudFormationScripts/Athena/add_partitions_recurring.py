import sys
import boto3
from datetime import datetime, timedelta
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

def get_immediate_folders(s3_path, s3_client):
    bucket_name = s3_path.strip("s3://").split("/")[0]
    prefix = remove_prefix(s3_path, "s3://" + bucket_name + "/")
    continuation_token = ""
    folders = []
    list_response = {}
    
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
            
        for item in list_response["CommonPrefixes"]:
            folders.append(remove_prefix(item["Prefix"], prefix).strip("/"))

        if "NextContinuationToken" in list_response:
            continuation_token = list_response["NextContinuationToken"]
        if list_response["IsTruncated"] == False:
            break
    
    return folders

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

def get_today_and_yesterday_partitions(s3_path):

    if not s3_path.endswith("/"):
        s3_path += "/"

    s3_client = boto3.client("s3")
    now = datetime.now()
    yesterday = now - timedelta(days = 1)

    # Create the S3 suffix for today's paths that we need to evaluate
    current_suffix = "/" + str(now.year) + "/" + str(now.month).zfill(2) + "/" + str(now.day).zfill(2) + "/"

    # Create the S3 suffix for yesterday's paths that we need to evaluate
    previous_suffix = "/" + str(yesterday.year) + "/" + str(yesterday.month).zfill(2) + "/" + str(yesterday.day).zfill(2) + "/"

    # Get the list of account ids in the bucket
    account_ids = get_immediate_folders(s3_path, s3_client)

    partitions = []

    for account_id in account_ids:
        path = s3_path + account_id + "/CloudTrail/"
        regions = get_immediate_folders(path, s3_client)

        for region in regions:
            full_path_current = path + region + current_suffix
            full_path_previous = path + region + previous_suffix

            partitions.append(full_path_current)
            partitions.append(full_path_previous)

    return partitions

# Get the partitions for today and yesterday
partitions = get_today_and_yesterday_partitions(source_s3_path)

if len(partitions) == 0:
    print("No partitions found to add.")
    exit
else:
    print("Found ", len(partitions), " partitions to review.")
    
    for part in partitions:
        print(part)

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