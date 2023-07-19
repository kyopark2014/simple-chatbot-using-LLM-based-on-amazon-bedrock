# lambda base image (python)
FROM amazon/aws-lambda-python:3.8

RUN /var/lang/bin/python3.8 -m pip install --upgrade pip
RUN wget https://db3lw8u6vdvwu.cloudfront.net/bedrock-sdk.zip
RUN unzip bedrock-python-sdk.zip -d bedrock-sdk
RUN rm -rf bedrock-python-sdk.zip
RUN pip install -U ./bedrock-sdk/botocore-1.29.162-py3-none-any.whl
RUN pip install -U ./bedrock-sdk/boto3-1.26.162-py3-none-any.whl
RUN pip install -U ./bedrock-sdk/awscli-1.27.162-py3-none-any.whl
RUN /var/lang/bin/python3.8 -m pip install PyPDF2
RUN /var/lang/bin/python3.8 -m pip install langchain
RUN rm -rf bedrock-sdk

WORKDIR /var/task/lambda-chat

COPY lambda_function.py /var/task/
COPY . .

CMD ["lambda_function.lambda_handler"]