# DynamoDB를 이용하여 Chat History 저장

DynamoDBChatMessageHistory을 이용하여 편리하게 저장을 할 수 있으나, 저장만 할뿐 DynamoDB에서 로드 할 수 없습니다. 복잡도 대비 효용성이 떨어져서 사용하지 않고자 합니다. 

아래와 같이 history를 DyanmoDB의 Table과 연결합니다.

```python
from langchain.memory.chat_message_histories import DynamoDBChatMessageHistory    
    my_key = {
    "user-id": userId,  # partition key
    "request-id": requestId, # sort key
}
message_history = DynamoDBChatMessageHistory(
    table_name = chatLogTableName,
    session_id = userId,
    key = my_key
)
history_memory = ConversationBufferMemory(
    chat_memory = message_history, return_messages = True
)
```

아래처럼 저장할 수 있습니다.

```python
history_memory.save_context({"input": text}, {"output": storedMsg})
```

읽을때는 아래와 같이 읽어옵니다. load_memory_variables()을 이용하여 body를 읽어온후에 history만을 추출합니다. 이때의 예는 아래와 같습니다.

```text
[HumanMessage(content='나는 서울에 살아', additional_kwargs=
{}
, example=False), AIMessage(content=' 네, 제임스님 서울에 사는군요. 서울은 우리나라 수도로 매우 발전된 도시에요. 경수님이 서울에서 어떤 점이 좋으신가요? 서울에는 맛있는 음식점도 많고 쇼핑할 수 있는 곳도 많죠.   서울 사는 것에 대한 경수님의 소감을 들어보고 싶습니다. 제가 서울에 대해 더 자세히 알려드릴 수 있어서 좋겠어요.', additional_kwargs=
{}
, example=False)]
```

여기서 contents를 가져오기 위해 langchain의 dumps()와 json.loads()를 이용해 json으로 변환합니다.

이때의 예는 아래와 같습니다.

```json
[
{
    "lc": 1,
    "type": "constructor",
    "id": [
        "langchain",
        "schema",
        "messages",
        "HumanMessage"
    ],
    "kwargs": {
        "content": "나는 서울에 살아",
        "additional_kwargs": {},
        "example": false
    }
}
, 
{
    "lc": 1,
    "type": "constructor",
    "id": [
        "langchain",
        "schema",
        "messages",
        "AIMessage"
    ],
    "kwargs": {
        "content": " 네, 제임스님 서울에 사는군요. 서울은 우리나라 수도로 매우 발전된 도시에요. 경수님이 서울에서 어떤 점이 좋으신가요? 서울에는 맛있는 음식점도 많고 쇼핑할 수 있는 곳도 많죠.   서울 사는 것에 대한 경수님의 소감을 들어보고 싶습니다. 제가 서울에 대해 더 자세히 알려드릴 수 있어서 좋겠어요.",
        "additional_kwargs": {},
        "example": false
    }
}
]
```


여기서 content를 아래처럼 추출합니다. 

```python
essages = history_memory.load_memory_variables({})['history']
print('messages: ', messages)

from langchain.load.dump import dumps
json_string = dumps(messages)
print('json_string: ', json_string)

json_str = json.loads(json_string)
print('json_str: ', json_str)

print('json[0]: ', json_str[0])

print('Human: ', json_str[0]['kwargs']['content'])
print('Assistant: ', json_str[1]['kwargs']['content'])
```
