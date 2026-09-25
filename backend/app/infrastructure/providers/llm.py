import os

from langchain_openai import AzureChatOpenAI, ChatOpenAI
from app.core.config import ENV_FILE

from dotenv import load_dotenv

load_dotenv(ENV_FILE)

class LanguageModel:
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0,
        fake_model: bool = False,
        provider: str | None = None,
    ):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()

        if fake_model:
            self.llm = type(
                "FakeLLM",
                (),
                {
                    "invoke": lambda self, prompt: type(
                        "FakeResponse",
                        (),
                        {"content": f"FAKE RESPONSE: {prompt}"},
                    )()
                },
            )()
            return

        if self.provider == "openai":
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=os.getenv("OPENAI_API_KEY"),
            )

        elif self.provider == "azure-openai":
            deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "").strip()
            if not deployment:
                raise ValueError(
                    "AZURE_OPENAI_CHAT_DEPLOYMENT must be set for Azure OpenAI."
                )
            self.llm = AzureChatOpenAI(
                model=model_name,
                azure_deployment=deployment,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                temperature=temperature,
            )

        else:
            raise ValueError(
                f"Unsupported LLM provider: {self.provider}. "
                "Supported providers: openai, azure-openai."
            )

    def predict(self, prompt: str) -> str:
        return self.llm.invoke(prompt).content


class _LazyLanguageModel:
    def __init__(self):
        self._model = None

    def predict(self, prompt: str) -> str:
        if self._model is None:
            self._model = LanguageModel()
        return self._model.predict(prompt)


LLM = _LazyLanguageModel()