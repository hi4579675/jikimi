class LlmService:
    async def analyze(self, text: str, legal_contexts: list) -> dict:
        raise NotImplementedError("LLM 서비스 미구현")
