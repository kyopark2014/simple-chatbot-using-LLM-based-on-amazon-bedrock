# Docker 환경 설정


## Dockerfile

```text
FROM amazon/aws-lambda-python:3.11

WORKDIR /var/task/lambda-chat

COPY lambda_function.py /var/task/
COPY test.py /var/task/   
COPY . ..

RUN /var/lang/bin/python3.11 -m pip install --upgrade pip

RUN /var/lang/bin/python3 -m pip install PyPDF2
RUN /var/lang/bin/python3 -m pip install langchain

RUN pip install -U /var/task/bedrock-sdk/boto3-1.28.55-py3-none-any.whl
RUN pip install -U /var/task/bedrock-sdk/botocore-1.31.55-py3-none-any.whl
RUN rm -rf /var/task/bedrock-sdk

CMD ["lambda_function.lambda_handler"]
```

## CDK 설정

```java
// Lambda for chat using langchain (container)
    const lambdaChatApi = new lambda.DockerImageFunction(this, `lambda-chat-for-${projectName}`, {
      description: 'lambda for chat api',
      functionName: `lambda-chat-api-for-${projectName}`,
      code: lambda.DockerImageCode.fromImageAsset(path.join(__dirname, '../../lambda-chat')),
      timeout: cdk.Duration.seconds(300),
      role: roleLambda,
      environment: {
        bedrock_region: bedrock_region,
        endpoint_url: endpoint_url,
        model_id: model_id,
        s3_bucket: s3Bucket.bucketName,
        s3_prefix: s3_prefix,
        callLogTableName: callLogTableName,
        accessType: accessType,
        conversationMode: conversationMode
      }
    });     
    lambdaChatApi.grantInvoke(new iam.ServicePrincipal('apigateway.amazonaws.com'));  
    s3Bucket.grantRead(lambdaChatApi); // permission for s3
    callLogDataTable.grantReadWriteData(lambdaChatApi); // permission for dynamo
```    
