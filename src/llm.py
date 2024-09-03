from langchain_ollama import ChatOllama
from config import OLLAMA_BASE_URL, MODEL_NAME


def get_llm(temperature: float, num_predict: int) -> ChatOllama:
    return ChatOllama(
        model=MODEL_NAME,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
        num_predict=num_predict,
    )
