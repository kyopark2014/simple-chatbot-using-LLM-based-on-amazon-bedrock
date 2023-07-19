FROM amazon/aws-lambda-python:3.8

WORKDIR /var/task/lambda-chat

COPY lambda_function.py /var/task/
COPY . .

RUN /var/lang/bin/python3.8 -m pip install --upgrade pip
RUN /var/lang/bin/python3.8 -m pip install botocore --upgrade 
#RUN /var/lang/bin/python3.8 -m pip install boto3 --upgrade  # 1.26.144
#RUN /var/lang/bin/python3.8 -m pip install boto3==1.28.5
RUN pip install --no-cache-dir boto3 --force-reinstall
RUN /var/lang/bin/python3.8 -m pip install -U /var/task/lambda-chat/bedrock-sdk/botocore-1.29.162-py3-none-any.whl
RUN /var/lang/bin/python3.8 -m pip install -U /var/task/lambda-chat/bedrock-sdk/boto3-1.26.162-py3-none-any.whl
RUN /var/lang/bin/python3.8 -m pip install -U /var/task/lambda-chat/bedrock-sdk/awscli-1.27.162-py3-none-any.whl --force-reinstall

RUN /var/lang/bin/python3.8 -m pip install PyPDF2
RUN /var/lang/bin/python3.8 -m pip install langchain
RUN rm -rf bedrock-sdk

CMD ["lambda_function.lambda_handler"]