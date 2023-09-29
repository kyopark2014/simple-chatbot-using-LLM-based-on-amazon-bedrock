# Bedrock SDK

## old 설치 방법

```text
cd ../lambda-chat
curl https://d2eo22ngex1n9g.cloudfront.net/Documentation/SDK/bedrock-python-sdk.zip --output bedrock-python-sdk.zip
unzip bedrock-python-sdk.zip -d bedrock-sdk
rm bedrock-python-sdk.zip
cd ../cdk-bedrock-simple-chatbot/
```

### 현재는 boto3와 botocore 업그레이드

```text
RUN /var/lang/bin/python3 -m pip install botocore --upgrade
RUN /var/lang/bin/python3 -m pip install boto3 --upgrade
```
