import os
from functools import lru_cache
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """Reusable OpenAI client wrapper for various LLM queries."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it directly.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.default_model = model

    def chat_completion(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict]] = None,
    ) -> str:
        """Send a chat completion request and return the response content."""
        response = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        )
        return response.choices[0].message.content

    def structured_output(
        self,
        messages: list[dict],
        response_format: type,
        model: Optional[str] = None,
        temperature: float = 0.3,
        tools: Optional[list[dict]] = None,
    ):
        """
        Send a chat completion request with structured output.
        
        Args:
            messages: List of chat messages
            response_format: A Pydantic model class for the structured response
            model: Model to use (defaults to instance default)
            temperature: Lower temperature for more consistent structured outputs
            tools: List of tools to enable for the model (e.g. web_search)
            
        Returns:
            Parsed Pydantic model instance
        """
        # Note: When using tools with parsed output, we rely on the model to use the tool 
        # internally if it's a built-in like web_search, or we might need to handle tool calls.
        # For OpenAI 'web_search' tool, it generates a response with citations.
        
        kwargs = {
            "model": model or self.default_model,
            "messages": messages,
            "response_format": response_format,
            "temperature": temperature,
        }
        if tools is not None:
            kwargs["tools"] = tools
            
        response = self.client.beta.chat.completions.parse(**kwargs)
        return response.choices[0].message.parsed

    def create_response(
        self,
        input_text: str,
        model: Optional[str] = None,
        tools: Optional[list[dict]] = None,
        reasoning: Optional[dict] = None,
        tool_choice: Optional[str] = None,
    ) -> str:
        """
        Use the OpenAI Responses API to generate content.
        This is the preferred way to use Web Search.
        """
        # Ensure we use a model compatible with Responses API if not specified
        # or rely on default. The user prompt suggests o4-mini, gpt-5 etc. 
        # But we will use the class default or passed model.
        
        response = self.client.responses.create(
            model=model or self.default_model,
            input=input_text,
            tools=tools,
            reasoning=reasoning,
            tool_choice=tool_choice,
        )
        return response.output_text


@lru_cache()
def get_llm_client() -> LLMClient:
    """Get a cached instance of the LLM client."""
    return LLMClient()

