# AWS Bedrock의 LLM을 이용한 Simple Chatbot 만들기

여기서는 AWS Bedrock의 LLM(Large language Model)을 이용하여 Prompt에 기반한 간단한 질문/답변을 보여주는 simple Chatbot을 구현합니다. 웹화면에서 문서버튼을 선택하여, Text, PDF와 같은 문서 파일을 업로드하면 문서 요약도 할 수 있습니다. LLM application 개발을 위해 LangChain을 활용하며, Bedrock은 여러가지의 LLM 모델을 예약어를 통해 바꾸어가면서 테스트할 수 있습니다. Bedrock은 Preview 아직 상태이므로 먼저 AWS를 통해 Preview Access 권한을 획득하여야 합니다. 챗봇을 위한 인프라는 AWS CDK를 이용하여 설치합니다. 사용자게 메시지 전송시 LLM을 통해 답변을 얻고 이를 화면에 보여줍니다. 또한 사용자가 pdf, txt, csv와 같은 파일을 업로드시 요약(summerization)을 할 수 있습니다. 입력한 모든 내용은 DynamoDB에 call log로 저장됩니다.

<img src="https://github.com/kyopark2014/simple-chatbot-using-LLM-based-on-amazon-bedrock/assets/52392004/4ae735e6-8e4b-4b59-9df1-739a84b395e0" width="700">

## Bedrock 모델정보 가져오기

Bedrock은 완전관리형 서비스로 API를 이용하여 접속하며, 여기서는 "us-west-2"를 이용하여 아래의 endpoint_url로 접속합니다. 이 주소는 preview 권한을 받을때 안내 받을 수 있습니다. 아래와 같이 get_bedrock_client()을 이용하여 client를 생성합니다. 이후 list_foundation_models()을 이용하여 현재 지원 가능한 LLM에 대한 정보를 획득할 수 있습니다.

```python
bedrock_region = "us-west-2" 
bedrock_config = {
    "region_name":bedrock_region,
    "endpoint_url":"https://prod.us-west-2.frontend.bedrock.aws.dev"
}
    
boto3_bedrock = bedrock.get_bedrock_client(
    region=bedrock_config["region_name"],
    url_override=bedrock_config["endpoint_url"])
    
modelInfo = boto3_bedrock.list_foundation_models()
print('models: ', modelInfo)
```

## LangChain 

아래와 같이 model id와 Bedrock client를 이용하여 LangChain을 정의합니다.

```python
modelId = 'amazon.titan-tg1-large'  # anthropic.claude-v1
llm = Bedrock(model_id=modelId, client=boto3_bedrock)
```

## 질문/답변하기 (Prompt)

LangChang을 이용하여 아래와 같이 간단한 질문과 답변을 Prompt을 이용하여 구현할 수 있습니다. 아래에서 입력인 text prompt를 LangChain 인터페이스를 통해 요청하면 Bedrock의 LLM 모델을 통해 답변을 얻을 수 있습니다.

```python
llm(text)
```

## 문서 요약하기 (Summerization)

아래와 같이 PyPDF2를 이용하여 S3로 업로드된 문서 파일을 읽어올 수 있습니다. 여기서는 pdf, txt, csv에 대한 파일을 로딩할 수 있습니다.

```python
import PyPDF2

s3r = boto3.resource("s3")
doc = s3r.Object(s3_bucket, s3_prefix + '/' + s3_file_name)

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
new_contents = str(contents).replace("\n", " ")
print('length: ', len(new_contents))
```

문서가 긴 경우에 token 크기를 고려하여 아래와 같이 chunk들로 분리합니다. 이후 Document를 이용하여 앞에 3개의 chunk를 문서로 만듧니다.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 0)
texts = text_splitter.split_text(new_contents)
print('texts[0]: ', texts[0])

docs = [
    Document(
        page_content = t
    ) for t in texts[: 3]
]
```

template를 정의하고 load_summarize_chain을 이용하여 summerization를 수행합니다.

```python
from langchain.chains.summarize import load_summarize_chain

prompt_template = """Write a concise summary of the following:

{ text }
        
    CONCISE SUMMARY """

PROMPT = PromptTemplate(template = prompt_template, input_variables = ["text"])
chain = load_summarize_chain(llm, chain_type = "stuff", prompt = PROMPT)
summary = chain.run(docs)
print('summary: ', summary)

if summary == '':  # error notification
    summary = 'Fail to summarize the document. Try agan...'
    return summary
else:
    return summary
```

## LLM 모델 변경

먼저 지원하는 LLM 모델의 종류를 확인후 아래와 같이 변경할 수 있습니다.

1) 모델 정보 확인하기

"list models"를 입력하면 아래와 같이 현재 지원되는 모델리스트를 보여줍니다. 

![image](https://github.com/kyopark2014/chatbot-based-on-bedrock-anthropic/assets/52392004/cc7b7c2d-9c11-4e0c-b09c-5fdb8459da0f)


2) 사용 모델 변경하기

"change the model to amazon.titan-e1t-medium"와 같이 모델명을 변경할 수 있습니다.

![image](https://github.com/kyopark2014/simple-chatbot-using-LLM-based-on-amazon-bedrock/assets/52392004/66ffbc00-d298-4a82-b758-799483f3518b)

현재 amazon.titan-e1t-medium으로 변경시 에러 발생하고 있습니다. 



## IAM Role

Bedrock의 IAM Policy는 아래와 같습니다.

```java
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "bedrock:*"
            ],
            "Resource": "*",
            "Effect": "Allow",
            "Sid": "BedrockFullAccess"
        }
    ]
}
```

이때의 Trust relationship은 아래와 같습니다.

```java
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "sagemaker.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        },
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "bedrock.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

Lambda가 Bedrock에 대한 Role을 가지도록 아래와 같이 설정합니다.

```python
const roleLambda = new iam.Role(this, "api-role-lambda-chat", {
    roleName: "api-role-lambda-chat-for-bedrock",
    assumedBy: new iam.CompositePrincipal(
        new iam.ServicePrincipal("lambda.amazonaws.com"),
        new iam.ServicePrincipal("sagemaker.amazonaws.com"),
        new iam.ServicePrincipal("bedrock.amazonaws.com")
    )
});
roleLambda.addManagedPolicy({
    managedPolicyArn: 'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
});

const SageMakerPolicy = new iam.PolicyStatement({  // policy statement for sagemaker
    actions: ['sagemaker:*'],
    resources: ['*'],
});
const BedrockPolicy = new iam.PolicyStatement({  // policy statement for sagemaker
    actions: ['bedrock:*'],
    resources: ['*'],
});
roleLambda.attachInlinePolicy( // add sagemaker policy
    new iam.Policy(this, 'sagemaker-policy-lambda-chat-bedrock', {
        statements: [SageMakerPolicy],
    }),
);
roleLambda.attachInlinePolicy( // add bedrock policy
    new iam.Policy(this, 'bedrock-policy-lambda-chat-bedrock', {
        statements: [BedrockPolicy],
    }),
);    
```

## 실습하기

### CDK를 이용한 인프라 설치

[인프라 설치](https://github.com/kyopark2014/chatbot-based-on-bedrock-anthropic/blob/main/deployment.md)에 따라 CDK로 인프라 설치를 진행합니다.


## Debugging

아래와 같이 [test.py](./lambda-chat/test.py)를 이용하여 local에서 컨테이너 이미지를 디버깅할 수 있습니다. 먼저 아래와 같이 이미지를 빌드합니다.

```text
docker build -t lambda_function-test:v1 .
```

Docker를 실행합니다.
```text
docker run -d -p 8080:8080 lambda_function-test:v1
```

아래와 같이 "docker ps"명령어로 Container ID를 확인 할 수 있습니다.
```text
CONTAINER ID   IMAGE          COMMAND                  CREATED         STATUS         PORTS                    NAMES
41e297948511   inference:v1   "/lambda-entrypoint.…"   6 seconds ago   Up 4 seconds   0.0.0.0:8080->8080/tcp   stupefied_carson
```

아래와 같이 Bash shell로 접속합니다.
```text
docker exec -it  41e297948511 /bin/bash
```

Container 접속 후 아래 명령어로 동작을 확인합니다.

```text
cd .. && python3 test.py
```





