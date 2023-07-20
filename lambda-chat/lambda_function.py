import json
import boto3
import os
import time
import datetime
from io import BytesIO
import PyPDF2
import csv
from langchain import PromptTemplate, SagemakerEndpoint
from langchain.llms.sagemaker_endpoint import LLMContentHandler
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain
import langchain
import sys
module_path = "."
sys.path.append(os.path.abspath(module_path))
from utils import bedrock, print_ww

s3 = boto3.client('s3')
s3_bucket = os.environ.get('s3_bucket') # bucket name
s3_prefix = os.environ.get('s3_prefix')
endpoint_name = os.environ.get('endpoint')
tableName = os.environ.get('tableName')
roleArn = os.environ.get('tableName')

# initiate llm model based on langchain
class ContentHandler(LLMContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, prompt: str, model_kwargs: dict) -> bytes:
        input_str = json.dumps({'inputs': prompt, 'parameters': model_kwargs})
        return input_str.encode('utf-8')
      
    def transform_output(self, output: bytes) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        return response_json[0]["generated_text"]

content_handler = ContentHandler()

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
        
llm = SagemakerEndpoint(
    endpoint_name = endpoint_name, 
    region_name = aws_region, 
    model_kwargs = parameters,
    content_handler = content_handler
)

def get_summary(file_type, s3_file_name):
    summary = ''
    
    s3r = boto3.resource("s3")
    doc = s3r.Object(s3_bucket, s3_prefix+'/'+s3_file_name)
    
    if file_type == 'pdf':
        contents = doc.get()['Body'].read()
        reader = PyPDF2.PdfReader(BytesIO(contents))
        
        raw_text = []
        for page in reader.pages:
            raw_text.append(page.extract_text())
        contents = '\n'.join(raw_text)    
        
    elif file_type == 'txt':        
        contents = doc.get()['Body'].read()
    elif file_type == 'csv':        
        body = doc.get()['Body'].read()
        reader = csv.reader(body)

        from langchain.document_loaders import CSVLoader
        contents = CSVLoader(reader)
    
    print('contents: ', contents)
    new_contents = str(contents).replace("\n"," ") 
    print('length: ', len(new_contents))

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=0)
    texts = text_splitter.split_text(new_contents) 
    print('texts[0]: ', texts[0])
        
    docs = [
        Document(
            page_content=t
        ) for t in texts[:3]
    ]
    prompt_template = """Write a concise summary of the following:

    {text}
        
    CONCISE SUMMARY """

    PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])
    chain = load_summarize_chain(llm, chain_type="stuff", prompt=PROMPT)
    summary = chain.run(docs)
    print('summary: ', summary)

    if summary == '':  # error notification
        summary = 'Fail to summarize the document. Try agan...'
        return summary
    else:
        return summary[1:len(summary)-1]   
     
def lambda_handler(event, context):
    print(event)

    requestid  = event['request-id']
    print('requestid: ', requestid)
    type  = event['type']
    print('type: ', type)
    body = event['body']
    print('body: ', body)
    
    start = int(time.time())    


    print(f"langchain version check: {langchain.__version__}")
    print(f"boto3 version check: {boto3.__version__}")

    # Bedrock Contiguration
    bedrock_region = "us-west-2" 
    """    
    bedrock_config = {
            "region_name":bedrock_region,
            "endpoint_url":"https://prod.us-west-2.frontend.bedrock.aws.dev"
        }
    
    boto3_bedrock = bedrock.get_bedrock_client(
        region=bedrock_config["region_name"],
        assumed_role=roleArn,
        url_override=bedrock_config["endpoint_url"])
    output_text = boto3_bedrock.list_foundation_models()
    print('models: ', output_text)
    """

    """
    bedrock_client = boto3.client(
        service_name='bedrock',
        region_name=bedrock_config["region_name"],
        endpoint_url=bedrock_config["endpoint_url"]
    )
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
    session = boto3.Session()
    if roleArn:
        print(f"  Using role: {roleArn}", end='')
        sts = session.client("sts")
        response = sts.assume_role(
            RoleArn=str(roleArn), #
            RoleSessionName="langchain-llm-1"
        )
        print(" ... successful!")
        boto3_kwargs['aws_access_key_id']=response['Credentials']['AccessKeyId']
        boto3_kwargs['aws_secret_access_key']=response['Credentials']['SecretAccessKey']
        boto3_kwargs['aws_session_token']=response['Credentials']['SessionToken']

    bedrock_client = session.client(
        service_name='bedrock',
        config=retry_config,
        region_name= bedrock_region,
        **boto3_kwargs
        )
    
    
    msg = ""
    if type == 'text':
        text = body
        msg = llm(text)
        
    elif type == 'document':
        object = body
    
        file_type = object[object.rfind('.')+1:len(object)]
        print('file_type: ', file_type)
        
        msg = get_summary(file_type, object)
            
    elapsed_time = int(time.time()) - start
    print("total run time(sec): ", elapsed_time)

    print('msg: ', msg)

    item = {
        'request-id': {'S':requestid},
        'type': {'S':type},
        'body': {'S':body},
        'msg': {'S':msg}
    }

    client = boto3.client('dynamodb')
    try:
        resp =  client.put_item(TableName=tableName, Item=item)
    except: 
        raise Exception ("Not able to write into dynamodb")
    
    print('resp, ', resp)
        
    return {
        'statusCode': 200,
        'msg': msg,
    }