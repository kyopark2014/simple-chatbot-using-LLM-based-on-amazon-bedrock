import json
import boto3
import os
import time
import datetime
from io import BytesIO
import PyPDF2
import csv
import sys

from langchain import PromptTemplate, SagemakerEndpoint
from langchain.llms.sagemaker_endpoint import LLMContentHandler
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain

from langchain.agents import create_csv_agent
from langchain.agents.agent_types import AgentType
from langchain.llms.bedrock import Bedrock

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
    
    boto3_bedrock = bedrock.get_bedrock_client(
        region=bedrock_config["region_name"],
        #assumed_role=roleArn,
        url_override=bedrock_config["endpoint_url"])
    
    output_text = boto3_bedrock.list_foundation_models()    
    print('models: ', output_text)

    # LangChaing
    modelId = 'amazon.titan-tg1-large'
    llm = Bedrock(model_id=modelId, client=boto3_bedrock)

    msg = llm(body) 
    print('output: ', msg)

    return {
        'statusCode': 200,
        'msg': msg,
    }