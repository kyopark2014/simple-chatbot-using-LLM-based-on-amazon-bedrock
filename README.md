# AWS Bedrock에서 Anthropic FM 기반의 한국어 챗봇 만들기

여기서는 AWS Bedrock의 Anthropic FM(Foundation Model)을 이용한 한국어 챗봇 만들기에 대해 설명합니다. 아직 Bedrock은 Preview 상태이므로 먼저 AWS를 통해 Preview Access 권한을 획득하여야 합니다. 


<img src="https://github.com/kyopark2014/chatbot-based-on-bedrock-anthropic/assets/52392004/770ecd69-3aee-49e4-b163-218d4c8a6078" width="650">

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

이후 text prompt에 대한 답변을 LangChain을 통해 얻을 수 있습니다.

```python
llm(text)
```

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

이미지를 빌드합니다.

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
python# lambda_function-test.py
```


