import json
import boto3
import os
import time
import datetime
from io import BytesIO
import PyPDF2
import csv
import sys
import re

from langchain import PromptTemplate, SagemakerEndpoint
from langchain.llms.sagemaker_endpoint import LLMContentHandler
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain

from langchain.agents import create_csv_agent
from langchain.agents.agent_types import AgentType
from langchain.llms.bedrock import Bedrock

s3 = boto3.client('s3')
s3_bucket = os.environ.get('s3_bucket') # bucket name
s3_prefix = os.environ.get('s3_prefix')
callLogTableName = os.environ.get('callLogTableName')
endpoint_url = os.environ.get('endpoint_url', 'https://prod.us-west-2.frontend.bedrock.aws.dev')
bedrock_region = os.environ.get('bedrock_region', 'us-west-2')
modelId = os.environ.get('model_id', 'amazon.titan-tg1-large')
print('model_id: ', modelId)
accessType = os.environ.get('accessType', 'aws')
conversationMode = os.environ.get('conversationMode', 'false')
methodOfConversation = 'PromptTemplate' # ConversationChain or PromptTemplate

# Bedrock Contiguration
bedrock_region = bedrock_region
bedrock_config = {
    "region_name":bedrock_region,
    "endpoint_url":endpoint_url
}
   
# supported llm list from bedrock
if accessType=='aws':  # internal user of aws
    boto3_bedrock = boto3.client(
        service_name='bedrock',
        region_name=bedrock_config["region_name"],
        endpoint_url=bedrock_config["endpoint_url"],
    )
else: # preview user
    boto3_bedrock = boto3.client(
        service_name='bedrock',
        region_name=bedrock_config["region_name"],
    )

modelInfo = boto3_bedrock.list_foundation_models()    
print('models: ', modelInfo)

HUMAN_PROMPT = "\n\nHuman:"
AI_PROMPT = "\n\nAssistant:"
def get_parameter(modelId):
    if modelId == 'amazon.titan-tg1-large': 
        return {
            "maxTokenCount":1024,
            "stopSequences":[],
            "temperature":0,
            "topP":0.9
        }
    elif modelId == 'anthropic.claude-v1' or modelId == 'anthropic.claude-v2':
        return {
            "stop_sequences": [HUMAN_PROMPT],
            #"model": "claude-2",
            "max_tokens_to_sample":1024,
        }
parameters = get_parameter(modelId)

llm = Bedrock(model_id=modelId, client=boto3_bedrock, model_kwargs=parameters)

# Conversation
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
if methodOfConversation == 'ConversationChain':
    memory = ConversationBufferMemory()
    conversation = ConversationChain(
        llm=llm, verbose=True, memory=memory
    )
elif methodOfConversation == 'PromptTemplate':
    # memory for conversation
    chat_memory = ConversationBufferMemory(human_prefix='Human', ai_prefix='Assistant')

def get_answer_using_chat_history(query, chat_memory):  
    condense_template = """Using the following conversation, answer friendly for the newest question. If you don't know the answer, just say that you don't know, don't try to make up an answer. You will be acting as a thoughtful advisor.
    
    {chat_history}
    
    Human: {question}

    Assistant:"""
    CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(condense_template)
        
    # extract chat history
    chats = chat_memory.load_memory_variables({})
    chat_history_all = chats['history']
    print('chat_history_all: ', chat_history_all)

    # use last two chunks of chat history
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000,chunk_overlap=0)
    texts = text_splitter.split_text(chat_history_all) 

    pages = len(texts)
    print('pages: ', pages)

    if pages >= 2:
        chat_history = f"{texts[pages-2]} {texts[pages-1]}"
    elif pages == 1:
        chat_history = texts[0]
    else:  # 0 page
        chat_history = ""
    print('chat_history:\n ', chat_history)

    # make a question using chat history
    if pages >= 1:
        result = llm(CONDENSE_QUESTION_PROMPT.format(question=query, chat_history=chat_history))
    else:
        result = llm(query)
    #print('result: ', result)

    return result    

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
    texts = text_splitter.split_text(new_contents).decode('utf-8')
    print('texts[0]: ', texts[0])
        
    docs = [
        Document(
            page_content=t
        ) for t in texts[:3]
    ]

    print('docs: ', docs)
    hanCount = len(re.findall(u'[\u3130-\u318F\uAC00-\uD7A3]+', texts))
    print('hanCount: ', hanCount)
    
    if modelId == 'anthropic.claude-v1' or modelId == 'anthropic.claude-v2':
        #prompt_template = """\n\nHuman: 다음 텍스트를 간결하게 요약하세오. 텍스트의 요점을 다루는 글머리 기호로 응답을 반환합니다.
        prompt_template = """\n\nHuman: 다음 텍스트를 요약해서 500자 이내로 설명하세오.

        {text}
        
        Assistant:"""
    else:
        prompt_template = """\n\nWrite a concise summary of the following:

        {text}
        
        Assistant:"""

    PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])
    chain = load_summarize_chain(llm, chain_type="stuff", prompt=PROMPT)
    summary = chain.run(docs)
    print('summary: ', summary)

    if summary == '':  # error notification
        summary = 'Fail to summarize the document. Try agan...'
        return summary
    else:
        # return summary[1:len(summary)-1]   
        return summary
    
def lambda_handler(event, context):
    print(event)
    userId  = event['user-id']
    print('userId: ', userId)
    requestId  = event['request-id']
    print('requestId: ', requestId)
    type  = event['type']
    print('type: ', type)
    body = event['body']
    print('body: ', body)

    global modelId, llm, parameters, conversation, conversationMode
    
    start = int(time.time())    

    msg = ""
    if type == 'text' and body[:11] == 'list models':
        msg = f"The list of models: \n"
        lists = modelInfo['modelSummaries']
        
        for model in lists:
            msg += f"{model['modelId']}\n"
        
        msg += f"current model: {modelId}"
        print('model lists: ', msg)    
    else:             
        if type == 'text':
            text = body

            querySize = len(text)
            textCount = len(text.split())
            print(f"query size: {querySize}, words: {textCount}")

            if text == 'enableConversationMode':
                conversationMode = 'true'
                msg  = "Conversation mode is enabled"
            elif text == 'disableConversationMode':
                conversationMode = 'false'
                msg  = "Conversation mode is disabled"
            else:            
                if conversationMode == 'true':
                    if methodOfConversation == 'ConversationChain':
                        msg = conversation.predict(input=text)
                    elif methodOfConversation == 'PromptTemplate':
                        msg = get_answer_using_chat_history(text, chat_memory)

                        storedMsg = str(msg).replace("\n"," ") 
                        chat_memory.save_context({"input": text}, {"output": storedMsg})     
                else:
                    msg = llm(HUMAN_PROMPT+text+AI_PROMPT)
            #print('msg: ', msg)
                
        elif type == 'document':
            object = body
        
            file_type = object[object.rfind('.')+1:len(object)]
            print('file_type: ', file_type)
            
            msg = get_summary(file_type, object)
                
        elapsed_time = int(time.time()) - start
        print("total run time(sec): ", elapsed_time)

        print('msg: ', msg)

        item = {
            'user-id': {'S':userId},
            'request-id': {'S':requestId},
            'type': {'S':type},
            'body': {'S':body},
            'msg': {'S':msg}
        }

        client = boto3.client('dynamodb')
        try:
            resp =  client.put_item(TableName=callLogTableName, Item=item)
        except: 
            raise Exception ("Not able to write into dynamodb")
        
        print('resp, ', resp)

    return {
        'statusCode': 200,
        'msg': msg,
    }
