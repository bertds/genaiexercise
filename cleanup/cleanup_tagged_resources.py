import re

import boto3
from botocore.exceptions import ClientError

aoss_client = boto3.client("opensearchserverless")
bedrock_agent_client = boto3.client("bedrock-agent")
iam_client = boto3.client("iam")
bedrock_client = boto3.client("bedrock")
lambda_client = boto3.client('lambda')
dynamodb_client = boto3.client('dynamodb')

def get_tagged_resources(name, value):
    """Find all resources with specified tag name and value"""
    client = boto3.client("resourcegroupstaggingapi")
    resources = []

    try:
        paginator = client.get_paginator("get_resources")
        for page in paginator.paginate(TagFilters=[{"Key": name, "Values": [value]}]):
            mapping_list = page["ResourceTagMappingList"]
            resources.extend([r["ResourceARN"] for r in mapping_list])
    except ClientError as e:
        print(f"Error finding tagged resources: {e}")

    try:
        paginator = iam_client.get_paginator("list_roles")
        for page in paginator.paginate():
            for role in page["Roles"]:
                tags = iam_client.list_role_tags(RoleName=role["RoleName"])["Tags"]
                if any(tag["Key"] == name and tag["Value"] == value for tag in tags):
                    resources.append(role["Arn"])
    except ClientError as e:
        print(f"Error listing roles: {e}")

    return resources


def parse_arn(arn):
    """Parses ARN like:
    arn:partition:service:region:account-id:resource
    arn:partition:service:region:account-id:resource-type:resource-id
    and provides service and resource. it includes resource-type:resource-id as resource
    """
    parts = arn.split(":")
    service = parts[2]
    resource = ":".join(parts[5:])
    return service, resource


def delete_collection(arn, service, resource):
    """Delete OpenSearch Serverless collection and associated policies"""
    match = re.match(r"^collection/(.+)", resource)
    if service == "aoss" and match:
        print(f"Deleting: {arn}")
        collection_id = match.group(1)

        # Show collection info
        collections = aoss_client.batch_get_collection(ids=[collection_id])[
            "collectionDetails"
        ]
        if len(collections) == 1:
            collection = collections[0]
            resource_name = f"collection/{collection['name']}"
            # Find and delete security (network/ access) policies for this collection
            for policy_type in ["encryption", "network"]:
                security_policies = aoss_client.list_security_policies(
                    type=policy_type, resource=[resource_name]
                )["securityPolicySummaries"]
                for policy in security_policies:
                    policy_name = policy["name"]
                    print(
                        f"-> Deleting OpenSearchServerless {policy_type} policy: {policy_name}"
                    )
                    aoss_client.delete_security_policy(
                        name=policy_name, type=policy_type
                    )
            access_policies = aoss_client.list_access_policies(
                type="data", resource=[resource_name]
            )["accessPolicySummaries"]
            for policy in access_policies:
                policy_name = policy["name"]
                print(f"-> Deleting OpenSearchServerless data policy: {policy_name}")
                aoss_client.delete_access_policy(name=policy_name, type="data")
            print(f"-> Deleting OpenSearch Serverless collection: {resource_name}")
            aoss_client.delete_collection(id=collection_id)


def delete_guardrail(arn, service, resource):
    """Delete Bedrock guardrail"""
    match = re.match(r"^guardrail/(.+)", resource)
    if service == "bedrock" and match:
        print(f"Deleting: {arn}")
        guardrail_id = match.group(1)
        print(f"-> Deleting guardrail: {guardrail_id}")
        bedrock_client.delete_guardrail(guardrailIdentifier=arn)

def delete_knowledgebase(arn, service, resource):
    """Delete Bedrock knowledge base and all data sources"""
    match = re.match(r"^knowledge-base/(.+)", resource)
    if service == "bedrock" and match:
        print(f"Deleting: {arn}")
        kb_id = match.group(1)
        kb = bedrock_agent_client.get_knowledge_base(knowledgeBaseId=kb_id)[
            "knowledgeBase"
        ]
        data_sources = bedrock_agent_client.list_data_sources(knowledgeBaseId=kb_id)[
            "dataSourceSummaries"
        ]
        for ds in data_sources:
            # Set deletion policy to RETAIN before deletion
            # Setting deletion policy to RETAIN for data source first
            ds_details = bedrock_agent_client.get_data_source(
                knowledgeBaseId=kb_id, dataSourceId=ds["dataSourceId"]
            )["dataSource"]
            bedrock_agent_client.update_data_source(
                knowledgeBaseId=kb_id,
                dataSourceId=ds["dataSourceId"],
                name=ds_details["name"],
                dataSourceConfiguration=ds_details["dataSourceConfiguration"],
                vectorIngestionConfiguration=ds_details["vectorIngestionConfiguration"],
                dataDeletionPolicy="RETAIN",
            )
            print(f"-> Deleting data source: {ds['name']}")
            bedrock_agent_client.delete_data_source(
                knowledgeBaseId=kb_id, dataSourceId=ds["dataSourceId"]
            )
        print(f"-> Deleting knowledge base: {kb['name']}")
        bedrock_agent_client.delete_knowledge_base(knowledgeBaseId=kb_id)


def delete_bucket(arn, service, resource):
    """Delete S3 bucket after emptying all objects"""
    if service == "s3":
        print(f"Deleting: {arn}")
        bucket_name = resource  # For S3, resource is just the bucket name
        s3_client = boto3.client("s3")

        # Empty the bucket first
        print(f"-> Deleting all contained objects")
        paginator = s3_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket_name):
            if "Contents" in page:
                objects = [{"Key": obj["Key"]} for obj in page["Contents"]]
                s3_client.delete_objects(
                    Bucket=bucket_name, Delete={"Objects": objects}
                )

        print(f"-> Deleting S3 bucket: {bucket_name}")
        s3_client.delete_bucket(Bucket=bucket_name)


def delete_roles(arn, service, resource):
    """Delete IAM role after detaching policies and removing from instance profiles"""
    match = re.match(r"^role/(.+)", resource)
    if service == "iam" and match:
        role_name = match.group(1)
        if role_name.startswith('service-role/'):
            role_name = role_name.replace('service-role/', '')

        print(f"Deleting: {arn}")

        # Detach all managed policies
        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)[
            "AttachedPolicies"
        ]
        for policy in attached_policies:
            print(f"-> Detaching managed policy: {policy['PolicyName']}")
            iam_client.detach_role_policy(
                RoleName=role_name, PolicyArn=policy["PolicyArn"]
            )

        # Delete all inline policies
        inline_policies = iam_client.list_role_policies(RoleName=role_name)[
            "PolicyNames"
        ]
        for policy_name in inline_policies:
            print(f"-> Deleting inline policy: {policy_name}")
            iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

        # Remove role from instance profiles
        try:
            instance_profiles = iam_client.list_instance_profiles_for_role(
                RoleName=role_name
            )["InstanceProfiles"]
            for profile in instance_profiles:
                print(
                    f"-> Removing role from instance profile: {profile['InstanceProfileName']}"
                )
                iam_client.remove_role_from_instance_profile(
                    InstanceProfileName=profile["InstanceProfileName"],
                    RoleName=role_name,
                )
        except ClientError:
            pass
        print(f"-> Deleting role: {role_name}")
        iam_client.delete_role(RoleName=role_name)


def delete_policy(arn, service, resource):
    """Delete IAM policy"""
    match = re.match(r"^policy/(.+)", resource)
    if service == "iam" and match:
        print(f"Deleting: {arn}")
        policy_name = match.group(1)
        versions = iam_client.list_policy_versions(PolicyArn=arn)['Versions']
        for version in versions:
            if not version['IsDefaultVersion']:
                print(f"-> Deleting IAM policy version: {version['VersionId']}")
                iam_client.delete_policy_version(
                    PolicyArn=arn,
                    VersionId=version['VersionId']
                )
        print(f"-> Deleting IAM policy: {policy_name}")
        iam_client.delete_policy(PolicyArn=arn)

def delete_function(arn, service, resource):
    """Delete Lambda function"""
    match = re.match(r"^function:(.+)", resource)
    if service == "lambda" and match:
        print(f"Deleting: {arn}")
        function_name = match.group(1)
        print(f"-> Deleting Lambda function: {function_name}")
        lambda_client.delete_function(FunctionName=function_name)

def delete_table(arn, service, resource):
    """Delete DynamoDB table"""
    match = re.match(r"^table/(.+)", resource)
    if service == "dynamodb" and match:
        print(f"Deleting: {arn}")
        table_name = match.group(1)
        print(f"-> Deleting DynamoDB table: {table_name}")
        dynamodb_client.delete_table(TableName=table_name)

def delete_agent(arn, service, resource):
    """Delete Bedrock Agent"""
    match = re.match(r"^agent/(.+)", resource)
    if service == "bedrock" and match:
        print(f"Deleting: {arn}")
        agent_id = match.group(1)
        print(f"-> Deleting Bedrock Agent: {agent_id}")
        bedrock_agent_client.delete_agent(agentId=agent_id)

def delete_resources(arns):
    """Delete all resources by ARN using appropriate deletion methods"""
    delete_actions = [
        delete_guardrail,
        delete_collection,
        delete_knowledgebase,
        delete_bucket,
        delete_function,
        delete_roles,
        delete_policy,
        delete_table,
        delete_agent
    ]

    for action in delete_actions:
        for arn in arns:
            service, resource = parse_arn(arn)
            action(arn, service, resource)
