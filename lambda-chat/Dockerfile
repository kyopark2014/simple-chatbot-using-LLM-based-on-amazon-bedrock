FROM amazon/aws-lambda-python:3.9

WORKDIR /var/task/lambda-chat

COPY lambda_function.py /var/task/
COPY test.py /var/task/   
COPY utils /var/task/utils
COPY . .

RUN /var/lang/bin/python3.9 -m pip install --upgrade pip

RUN /var/lang/bin/python3 -m pip install PyPDF2
RUN /var/lang/bin/python3 -m pip install langchain

#RUN /var/lang/bin/python3 -m pip install -U ./bedrock-sdk/botocore-1.29.162-py3-none-any.whl
#RUN /var/lang/bin/python3 -m pip install -U ./bedrock-sdk/boto3-1.26.162-py3-none-any.whl
#RUN /var/lang/bin/python3 -m pip install -U ./bedrock-sdk/awscli-1.27.162-py3-none-any.whl

CMD ["lambda_function.lambda_handler"]