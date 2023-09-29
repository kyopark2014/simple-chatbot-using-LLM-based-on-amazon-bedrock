# PromptTemplate을 이용한 chat history 구현

아래는 ConversationChain이 아닌 PromptTemplate을 이용해 chat history를 구현한 예입니다. Bedrock SDK 업그레이드후에 claude관련 변경으로 아래 코드는 현재 사용 불가상태입니다.

```python
chat_memory = ConversationBufferMemory(human_prefix='Human', ai_prefix='Assistant')
map[userId] = chat_memory
print('chat_memory does not exist. create new one!')

allowTime = getAllowTime()
load_chatHistory(userId, allowTime, chat_memory)

msg = get_answer_using_chat_history(text, chat_memory)

storedMsg = str(msg).replace("\n"," ") 
chat_memory.save_context({"input": text}, {"output": storedMsg})

def get_answer_using_chat_history(query, chat_memory):  
    # check korean
    pattern_hangul = re.compile('[\u3131-\u3163\uac00-\ud7a3]+')
    word_kor = pattern_hangul.search(str(query))
    print('word_kor: ', word_kor)

    if word_kor:
        #condense_template = """\n\nHuman: 아래 문맥(context)을 참조했음에도 답을 알 수 없다면, 솔직히 모른다고 말합니다.
        condense_template = """\n\nHuman: 다음은 Human과 Assistant의 친근한 대화입니다. Assistant은 상황에 맞는 구체적인 세부 정보를 충분히 제공합니다. 아래 문맥(context)을 참조했음에도 답을 알 수 없다면, 솔직히 모른다고 말합니다.

        {chat_history}
        
        Human: {question}

        Assistant:"""
    else:
        condense_template = """\n\nHuman: Using the following conversation, answer friendly for the newest question. If you don't know the answer, just say that you don't know, don't try to make up an answer. You will be acting as a thoughtful advisor.

        {chat_history}
        
        Human: {question}

        Assistant:"""
    
    CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(condense_template)
        
    # extract chat history
    chats = chat_memory.load_memory_variables({})
    chat_history_all = chats['history']
    print('chat_history_all: ', chat_history_all)

    # use last two chunks of chat history
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=0,
        separators=["\n\n", "\n", ".", " ", ""],
        length_function = len)
    texts = text_splitter.split_text(chat_history_all) 

    pages = len(texts)
    print('pages: ', pages)

    if pages >= 2:
        chat_history = f"{texts[pages-2]} {texts[pages-1]}"
    elif pages == 1:
        chat_history = texts[0]
    else:  # 0 page
        chat_history = ""
    print('chat_history:\n ', chat_history)

    # make a question using chat history
    result = llm(CONDENSE_QUESTION_PROMPT.format(question=query, chat_history=chat_history))

    return result    
```
