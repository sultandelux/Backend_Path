import re
import os
import logging

from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.llms import OpenAI


class OpenAIService:
    def professions_list(self, galluptext, top3prof, MBTI_str, MIT):
        openai_api_key = os.getenv("OPENAI_API_KEY")
        llm = OpenAI(openai_api_key=openai_api_key)
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    "you are an expert that uses following test results: 1. clifton strength34, 2. myers-briggs, 3. Multiple Intelligences Test Based on the work of Howard Gardner. you help people to understand themselves, their strengths and blind spots, and give career advice based on these test results. "
                ),
                MessagesPlaceholder(variable_name="history"),
                HumanMessagePromptTemplate.from_template("{input}"),
            ]
        )

        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        memory = ConversationBufferMemory(return_messages=True)
        conversation = ConversationChain(memory=memory, prompt=prompt, llm=llm)

        text1 = conversation.predict(
            input=f"Here is my gallup strengths in order from 1st to 15 th: {galluptext}, MBTI: {MBTI_str}, Multiple Intelligences Test result: {MIT} consider only resutls higher than 60%. Now I want you to fully describe me as a person taking into consideration all the provided information above including clifton strength34, MBTI, please don't describe all my personal test results, I just need comprahensive analysis of my personality based on them, minimal length of it should be 600 words, at the end should be conclusion"
        )
        text2 = re.sub(r'^.*?\n', '\n', conversation.predict(input=f"continue to say about which top 3 potential career field paths may be considered, minimum length of report should be 400 words, at the beggining it should have small introduction, bold names of the Fields"))
        text3 = re.sub(r'^.*?\n', '\n', conversation.predict(input=f"Based on my gallup strengths and Multiple Intelligences Test results analyse my top 5 selected professions {top3prof}, minimum length of report should be 400 words, at the beggining it should have small introduction, bold names of the professions"))
        return text1, text2, text3
