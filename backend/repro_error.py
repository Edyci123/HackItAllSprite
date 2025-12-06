
from pydantic import BaseModel
from llm_client import get_llm_client
import os

class TestModel(BaseModel):
    foo: str

client = get_llm_client()

print("Testing structured_output with tools=None...")
try:
    result = client.structured_output(
        messages=[{"role": "user", "content": "say hello"}],
        response_format=TestModel,
        tools=None
    )
    print("Success:", result)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
