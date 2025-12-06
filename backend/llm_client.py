import os
from functools import lru_cache
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """Reusable OpenAI client wrapper for various LLM queries."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it directly.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.default_model = model

    def chat_completion(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        """Send a chat completion request and return the response content."""
        response = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def structured_output(
        self,
        messages: list[dict],
        response_format: type,
        model: str | None = None,
        temperature: float = 0.3,
    ):
        """
        Send a chat completion request with structured output.
        
        Args:
            messages: List of chat messages
            response_format: A Pydantic model class for the structured response
            model: Model to use (defaults to instance default)
            temperature: Lower temperature for more consistent structured outputs
            
        Returns:
            Parsed Pydantic model instance
        """
        response = self.client.beta.chat.completions.parse(
            model=model or self.default_model,
            messages=messages,
            response_format=response_format,
            temperature=temperature,
        )
        return response.choices[0].message.parsed


@lru_cache()
def get_llm_client() -> LLMClient:
    """Get a cached instance of the LLM client."""
    return LLMClient()

