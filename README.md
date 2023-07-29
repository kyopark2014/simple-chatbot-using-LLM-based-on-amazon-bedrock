# Amazon Bedrock의 LLM을 이용한 Simple Chatbot 만들기

여기서는 Amazon Bedrock의 LLM(Large language Model)을 이용하여 Prompt에 기반한 간단한 질문/답변을 보여주는 simple chatbot을 구현합니다. 브라우저에서 chatbot으로 메시지를 전송하면, LLM을 통해 답변을 얻고 이를 화면에 보여줍니다. 입력한 모든 내용은 DynamoDB에 call log로 저장됩니다. 또한 파일 버튼을 선택하여, TXT, PDF, CSV와 같은 문서 파일을 Amazon S3로 업로드하고, 텍스트를 추출하여 문서 요약(Summerization) 기능을 사용할 수 있습니다.

LLM 어플리케이션 개발을 위해 LangChain을 활용하였으며, Bedrock이 제공하는 LLM 모델을 확인하고, 필요시 변경할 수 있습니다. Chatbot API를 테스트 하기 위하여 Web Client를 제공합니다. AWS CDK를 이용하여 chatbot을 위한 인프라를 설치하면, ouput 화면에서 브라우저로 접속할 수 있는 URL을 알수 있습니다. Bedrock은 아직 Preview로 제공되므로, AWS를 통해 Preview Access 권한을 획득하여야 사용할 수 있습니다.

<img src="https://github.com/kyopark2014/simple-chatbot-using-LLM-based-on-amazon-bedrock/assets/52392004/a62d871e-ad88-400b-9d80-6cdf8b3d63a7" width="800">

## Bedrock 모델 정보 가져오기

Bedrock은 완전관리형 서비스로 API를 이용하여 접속하며, 여기서는 "us-west-2"를 이용하여 아래의 endpoint_url로 접속합니다. 이 주소는 preview 권한을 받을때 안내 받을 수 있습니다. 아래와 같이 get_bedrock_client()을 이용하여 client를 생성합니다. 이후 list_foundation_models()을 이용하여 현재 지원 가능한 LLM에 대한 정보를 획득할 수 있습니다.

```python
import boto3
from utils import bedrock

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
from langchain.llms.bedrock import Bedrock

modelId = 'amazon.titan-tg1-large'  # anthropic.claude-v1
llm = Bedrock(model_id=modelId, client=boto3_bedrock)
```

## 질문/답변하기 (Prompt)

LangChang을 이용하여 아래와 같이 간단한 질문과 답변을 Prompt을 이용하여 구현할 수 있습니다. 아래에서 입력인 text prompt를 LangChain 인터페이스를 통해 요청하면 Bedrock의 LLM 모델을 통해 답변을 얻을 수 있습니다.

```python
llm(text)
```


## 문서 요약하기 (Summerization)

### 파일 읽어오기

S3에서 아래와 같이 Object를 읽어옵니다.

```python
s3r = boto3.resource("s3")
doc = s3r.Object(s3_bucket, s3_prefix + '/' + s3_file_name)
```

pdf파일은 PyPDF2를 이용하여 S3에서 직접 읽어옵니다.

```python
import PyPDF2

contents = doc.get()['Body'].read()
reader = PyPDF2.PdfReader(BytesIO(contents))

raw_text = []
for page in reader.pages:
    raw_text.append(page.extract_text())
contents = '\n'.join(raw_text)    
```

파일 확장자가 txt이라면 body에서 추출하여 사용합니다.
```python
contents = doc.get()['Body'].read()
```

파일 확장자가 csv일 경우에 CSVLoader을 이용하여 읽어옵니다.

```python
from langchain.document_loaders import CSVLoader
body = doc.get()['Body'].read()
reader = csv.reader(body)
contents = CSVLoader(reader)
```

### 텍스트 나누기 

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

### Template를 이용하여 요약하기

Template를 정의하고 load_summarize_chain을 이용하여 summerization를 수행합니다.

```python
from langchain import PromptTemplate
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

Lambda가 Bedrock에 대한 Role을 가지도록 아래와 같이 CDK에서 IAM Role을 생성할 수 있습니다.

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

[인프라 설치](https://github.com/kyopark2014/chatbot-based-on-bedrock-anthropic/blob/main/deployment.md)에 따라 CDK로 인프라 설치를 진행합니다. [CDK 구현 코드](./cdk-bedrock-simple-chatbot/README.md)에서는 Typescript로 인프라를 정의하는 방법에 대해 상세히 설명하고 있습니다.

### 실행결과

아래와 같이 이메일 작성을 요청합니다.

```text
Write an email from Bob, Customer Service Manager, to the customer "John Doe" 
who provided negative feedback on the service provided by our customer support 
engineer
```

요청에 맞춰서 적절한 이메일 문장을 생성하였습니다.

![image](https://github.com/kyopark2014/simple-chatbot-using-LLM-based-on-amazon-bedrock/assets/52392004/c3d2eb31-28de-451e-9069-3b0400c36d1f)


아래와 같이 코드 생성을 요청합니다.

```text
Generate and return the code for each module using the programming language and programming framework requested in. Modify this code and return markdowns for each module using the suggestions in: Python Streamlit code for a banking app using DynamoDB
```

이때의 결과는 아래와 같습니다.

![image](https://github.com/kyopark2014/chatbot-based-on-Falcon-FM/assets/52392004/ed53c663-e035-49dc-9b77-b54dae565cb7)

## 브라우저에서 Chatbot 동작 시험시 주의할점

Chatbot API를 테스트하기 위해 제공하는 Web client는 일반적인 채팅 App처럼 세션 방식(web socket등)이 아니라 RESTful API를 사용합니다. 따라서 아래와 같은 특징이 있습니다.

1) LLM에서 응답이 일정시간(30초)이상 지연되는 경우에 답변을 볼 수 없습니다. 브라우저 자체적인 timeout으로 인하여 30초 이상인 경우에 client에서 더이상 응답을 받을 수 없습니다. 이때 응답을 확인하기 위해서는 CloudWatch에서 [lambda-chat](./lambda-chat/lambda_function.py)의 로그를 확인하거나, DynamoDB에 저장된 call log를 확인합니다.
2) 한번에 전달할 수 있는 Lambda Payload 사이즈 제한으로 5MB이하의 파일만 업로드가 가능합니다. 

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





