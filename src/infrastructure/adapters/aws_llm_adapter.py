class AWSBedrockLLMAdapter:
    """LLMPort implementation using AWS Bedrock Converse API."""

    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        region: str = "us-east-1",
        model: str = "anthropic.claude-3-haiku-20240307-v1:0",
    ) -> None:
        try:
            import boto3
            self._client = boto3.client(
                "bedrock-runtime",
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=region,
            )
        except ImportError:
            raise RuntimeError("boto3 not installed: pip install boto3>=1.35.0")
        self._model = model

    def chat(self, messages: list[dict], max_tokens: int = 1000) -> str:
        system_msgs = [{"text": m["content"]} for m in messages if m["role"] == "system"]
        conv_msgs = [
            {"role": m["role"], "content": [{"text": m["content"]}]}
            for m in messages
            if m["role"] != "system"
        ]

        kwargs: dict = {
            "modelId": self._model,
            "messages": conv_msgs,
            "inferenceConfig": {"maxTokens": max_tokens},
        }
        if system_msgs:
            kwargs["system"] = system_msgs

        response = self._client.converse(**kwargs)
        return response["output"]["message"]["content"][0]["text"]

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Use SentenceTransformerEmbedder for embeddings.")
