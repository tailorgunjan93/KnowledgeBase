def _aws_error(err: Exception, model: str) -> ValueError:
    s = str(err)
    t = type(err).__name__
    if "ThrottlingException" in t or "TooManyRequestsException" in t or "429" in s:
        return ValueError(
            "AWS Bedrock rate limit exceeded. Please wait and try again."
        )
    if "UnrecognizedClientException" in t or "InvalidSignatureException" in t or "AuthFailure" in s:
        return ValueError(
            "AWS credentials are invalid. Go to Settings → AWS Bedrock and check your Access Key and Secret Key."
        )
    if "AccessDeniedException" in t or "403" in s:
        return ValueError(
            f"AWS Bedrock access denied for model '{model}'. "
            "Ensure your IAM user has 'bedrock:InvokeModel' permission and the model is enabled in your AWS region."
        )
    if "ValidationException" in t and "model" in s.lower():
        return ValueError(
            f"AWS Bedrock model '{model}' is not available in your region. "
            "Go to Settings → AWS Bedrock and select a different model or region."
        )
    if "ResourceNotFoundException" in t or "404" in s:
        return ValueError(
            f"AWS Bedrock model '{model}' was not found. "
            "Go to Settings → AWS Bedrock and select a different model."
        )
    return ValueError(f"AWS Bedrock error: {s}")


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

        try:
            response = self._client.converse(**kwargs)
        except Exception as err:
            raise _aws_error(err, self._model) from err

        return response["output"]["message"]["content"][0]["text"]

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Use SentenceTransformerEmbedder for embeddings.")
