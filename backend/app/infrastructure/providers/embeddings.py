import os

from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings


_embedding = None


def get_embedding():
    global _embedding
    if _embedding is None:
        provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
        if provider == "openai":
            _embedding = OpenAIEmbeddings(check_embedding_ctx_length=False)
        elif provider == "azure-openai":
            deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "").strip()
            if not deployment:
                raise ValueError(
                    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT must be set for Azure OpenAI embeddings."
                )
            _embedding = AzureOpenAIEmbeddings(
                azure_deployment=deployment,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
                check_embedding_ctx_length=False,
            )
        else:
            raise ValueError("LLM_PROVIDER must be 'openai' or 'azure-openai'")
    return _embedding