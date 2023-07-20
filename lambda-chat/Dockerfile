FROM amazon/aws-lambda-python:3.9

WORKDIR /var/task/lambda-chat

COPY lambda_function.py /var/task/
COPY utils/ /var/task/utils/
COPY . .

RUN /var/lang/bin/python3.9 -m pip install --upgrade pip
RUN /var/lang/bin/python3.9 -m pip install botocore --upgrade -t /var/task/
RUN /var/lang/bin/python3.9 -m pip install boto3 --upgrade -t /var/task/
RUN /var/lang/bin/python3.9 -m pip install -U /var/task/lambda-chat/bedrock-sdk/botocore-1.29.162-py3-none-any.whl -t /var/task/ 
RUN /var/lang/bin/python3.9 -m pip install -U /var/task/lambda-chat/bedrock-sdk/boto3-1.26.162-py3-none-any.whl -t /var/task/ 
RUN /var/lang/bin/python3.9 -m pip install -U /var/task/lambda-chat/bedrock-sdk/awscli-1.27.162-py3-none-any.whl -t /var/task/ 

RUN /var/lang/bin/python3.9 -m pip install PyPDF2
RUN /var/lang/bin/python3.9 -m pip install langchain
RUN rm -rf bedrock-sdk

#RUN /var/lang/bin/python3.9 -m pip install -U boto3 -t /var/task/

CMD ["lambda_function.lambda_handler"]