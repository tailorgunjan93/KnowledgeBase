"""Generation Worker for LLM response generation."""

import os

from ..workers import Task, TaskResult, Worker, WorkerType


class GenerationWorker(Worker):
    """Worker for generating responses using LLM."""

    def __init__(self, model: str = "openai/gpt-oss-120b"):
        super().__init__(WorkerType.GENERATION)
        self.model = model
        self.client = None

    def _get_client(self):
        """Get or create LLM client."""
        if self.client is None:
            try:
                from groq import Groq

                api_key = os.getenv("GROQ_API_KEY", "")
                if api_key:
                    self.client = Groq(api_key=api_key)
            except ImportError:
                pass
        return self.client

    async def process(self, task: Task) -> TaskResult:
        """Generate response using LLM."""
        try:
            query = task.input_data["query"]
            context = task.input_data.get("context", [])
            system_prompt = task.input_data.get(
                "system_prompt",
                "You are a helpful AI assistant. Use the provided context to answer questions.",
            )

            messages = [{"role": "system", "content": system_prompt}]

            if context:
                context_str = "\n\n".join(
                    [
                        f"Source {i + 1}: {c.get('text', '')}"
                        for i, c in enumerate(context[:3])
                    ]
                )
                messages.append(
                    {"role": "system", "content": f"Context:\n{context_str}"}
                )

            messages.append({"role": "user", "content": query})

            client = self._get_client()
            if client is None:
                return TaskResult(
                    task.task_id,
                    False,
                    error="LLM client not available. Set GROQ_API_KEY.",
                )

            response = client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.3, max_tokens=1024
            )

            if not response.choices:
                return TaskResult(
                    task.task_id, False, error="LLM returned no response choices"
                )

            return TaskResult(
                task.task_id, True, {"response": response.choices[0].message.content}
            )
        except Exception as e:
            return TaskResult(task.task_id, False, error=str(e))
