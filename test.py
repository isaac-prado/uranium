import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL_NAME"),
    temperature=0,
)

response = model.invoke("Explique em uma frase o que é LangGraph.")

print(response.content)