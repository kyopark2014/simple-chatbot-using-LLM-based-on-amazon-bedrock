import json
import boto3
import os
import time
import datetime
from io import BytesIO
import PyPDF2
import csv
import sys
module_path = "."
sys.path.append(os.path.abspath(module_path))
from utils import bedrock, print_ww

s3 = boto3.client('s3')
s3_bucket = os.environ.get('s3_bucket') # bucket name
s3_prefix = os.environ.get('s3_prefix')
endpoint_name = os.environ.get('endpoint')
tableName = os.environ.get('tableName')
roleArn = os.environ.get('roleArn')
print('roleArn: ', roleArn)

aws_region = boto3.Session().region_name

parameters = {
    "max_new_tokens": 512,
    "return_full_text": False,
    "do_sample": False,
    "temperature": 0.5,
    "repetition_penalty": 1.03,
    "top_p": 0.9,
    "top_k":1,
    "stop": ["<|endoftext|>", "</s>"]
}        
        
def lambda_handler(event, context):
    print(event)
    requestid  = event['request-id']
    print('requestid: ', requestid)
    type  = event['type']
    print('type: ', type)
    body = event['body']
    print('body: ', body)
    
    start = int(time.time())    

    print(f"boto3 version check: {boto3.__version__}")
     
    # Bedrock Contiguration
    bedrock_region = "us-west-2" 
    bedrock_config = {
            "region_name":bedrock_region,
            "endpoint_url":"https://prod.us-west-2.frontend.bedrock.aws.dev"
        }
    
    # guide1
    bedrock_region = "us-west-2" 

    is_internal_use = True # 내부 직원 용
    # is_internal_use = False # 고객 용

    if bedrock_region == "us-east-1":    
        bedrock_config = {
            "region_name":bedrock_region,
            "endpoint_url":"https://bedrock.us-east-1.amazonaws.com"
        }
    elif bedrock_region == "us-west-2":  
        bedrock_config = {
            "region_name":bedrock_region,
            "endpoint_url":"https://prod.us-west-2.frontend.bedrock.aws.dev"
        }
    
    if is_internal_use:
        bedrock_client = boto3.client(
            service_name='bedrock',
            region_name=bedrock_config["region_name"],
            endpoint_url=bedrock_config["endpoint_url"]
        )
    else:
        bedrock_client = boto3.client(
            service_name='bedrock',
            region_name=bedrock_config["region_name"]
        ) 

    bedrock_client = boto3.client(
        service_name='bedrock',
        region_name=bedrock_config["region_name"],
        endpoint_url=bedrock_config["endpoint_url"]
    )

    output_text = bedrock_client.list_foundation_models()
    print('output: ', output_text)


    """
    bedrock_client = boto3.client(
        service_name='bedrock',
        region_name=bedrock_config["region_name"],
        endpoint_url=bedrock_config["endpoint_url"]
    )
    """
    
    """
    from botocore.config import Config
    retry_config = Config(
        region_name = bedrock_region,
        retries = {
            'max_attempts': 10,
            'mode': 'standard'
        }
    )

    boto3_kwargs = {}
    session = boto3.Session(profile_name="bedrock")
    if roleArn:
        print('role: ', roleArn)
        sts = session.client("sts")
        response = sts.assume_role(
            RoleArn=str(roleArn), #
            RoleSessionName="langchain-llm-1"
        )
        print('sts: ', response)

        boto3_kwargs['aws_access_key_id']=response['Credentials']['AccessKeyId']
        boto3_kwargs['aws_secret_access_key']=response['Credentials']['SecretAccessKey']
        boto3_kwargs['aws_session_token']=response['Credentials']['SessionToken']

    bedrock_client = session.client(
        service_name='bedrock',
        config=retry_config,
        region_name= bedrock_region,
        **boto3_kwargs
        )
    output_text = bedrock_client.list_foundation_models()
    print('list_foundation_models: ', output_text)
    """
    
   
    return {
        'statusCode': 200,
        'msg': output_text,
    }