import os
from fastapi import Depends
from typing import Any

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Pinecone
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import DirectoryLoader
import pinecone
import logging
from app.auth.adapters.jwt_service import JWTData
from app.auth.router.dependencies import parse_jwt_user_data

from ..service import Service, get_service
from . import router


@router.get("/{pdf_id:str}/pdf_bot")
def get_pdf_similarity(
    bot_question: str,
    pdf_id: str,
    jwt_data: JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
) -> Any:
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENV = os.getenv("PINECONE_ENV")
    pdf_data = svc.repository.get_pdf_url(pdf_id=pdf_id, user_id=jwt_data.user_id)
    #logging.info(docs[0])
    MBTI_str = pdf_data.get("MBTI")
    MIT_str = pdf_data.get("MIT")
    best_themes = pdf_data.get("best_themes")
    embeddings = OpenAIEmbeddings()
    pdf_tokens = pdf_data.get("tokens_used")
    history = pdf_data.get("chat_hsitory")

    pinecone.init(
        api_key=PINECONE_API_KEY,  # find at app.pinecone.io
        environment=PINECONE_ENV,  # next to api key in console
    )
    index_name = "langchain"

    if pdf_tokens == 0:
        loader = DirectoryLoader("txt_files")
        documents = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(documents)
        index = pinecone.Index(index_name) 
        index.delete(deleteAll=True)
        #pinecone.create_index(index_name, dimension=1536, metric="cosine")
        texts = [d.page_content for d in docs]
        metadatas = [d.metadata for d in docs]

        docsearch = Pinecone.from_texts(
            texts,
            embeddings,
            metadatas,
            index_name=index_name,
        )

        os.remove(f"txt_files/{pdf_id}_comments.txt")

    elif 0 < pdf_tokens <= 20000:
        docsearch = Pinecone.from_existing_index(index_name, embeddings)

    else:
        return "You have exceeded your token limit!"

    query = "cybersecurity"
    docs = docsearch.similarity_search(query)
    #logging.info(docs)
    chain = RetrievalQAWithSourcesChain.from_chain_type(
        ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0),
        chain_type="stuff",
        retriever=docsearch.as_retriever(),
    )
    user_input = bot_question + f"(just remember that my top 15 gallup themes: {best_themes} ,MBTI {MBTI_str} and MIT: {MIT_str})"

    #history_str = ','.join(history)

    result = chain({"question": user_input, "chat_history": history}, return_only_outputs=True)
    answer = result["answer"]

    if user_input == "zero" + f"(just remember that my top 15 gallup themes: {best_themes} ,MBTI {MBTI_str} and MIT: {MIT_str})":
        history = ""
    else:
        history += f"\n user: {user_input}  \n bot: {answer}"
        
    logging.info(history)
    pdf_tokens += len(user_input) + len(answer)
    svc.repository.update_pdf_by_id(
        pdf_id=pdf_id, user_id=jwt_data.user_id, data={"tokens_used": pdf_tokens}
    )
    svc.repository.update_pdf_by_id(
        pdf_id=pdf_id, user_id=jwt_data.user_id, data={"chat_hsitory": history}
    )

    return answer


#print("Source: " + result["sources"], f"Tokens left: {1500 - round(n/4)}")