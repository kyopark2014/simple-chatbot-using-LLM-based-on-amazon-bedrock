# Bedrock SDK

Boto3 1.28.57 이하에서 Bedrock SDK는 아래처럼 다운로드하여 설치합니다. 

## SDK 설치 방법

최신 Boto3, Botocore를 사용시 아래 과정없이 가능합니다. 

```text
cd ../lambda-chat
curl https://d2eo22ngex1n9g.cloudfront.net/Documentation/SDK/bedrock-python-sdk.zip --output bedrock-python-sdk.zip
unzip bedrock-python-sdk.zip -d bedrock-sdk
rm bedrock-python-sdk.zip
cd ../cdk-bedrock-simple-chatbot/
```

### Boto3와 botocore 업그레이드 방법

```text
RUN /var/lang/bin/python3 -m pip install botocore --upgrade
RUN /var/lang/bin/python3 -m pip install boto3 --upgrade
```
