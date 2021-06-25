SELECT * FROM "cloudtrail"."cloudtrail_logs_athena_flat" WHERE ltrim(rtrim(replace(replace(replace(vpcendpointid,chr(9),''),chr(10),''),chr(13),''))) <> '' AND 'vpcendpointid' IS NOT NULL;
