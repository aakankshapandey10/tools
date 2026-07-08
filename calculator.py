import ast
import operator
import os

from anthropic import AnthropicFoundry
from dotenv import load_dotenv

load_dotenv()  # loads variables from a .env file into the environment

client = AnthropicFoundry(
    api_key=os.getenv("AZURE_API_KEY"),
    base_url=os.getenv("AZURE_BASE_URL"),
)

MODEL = "claude-haiku-4-5"  # or "claude-2.0" or "claude-instant-v1.1"

# we are making a calculator tool that can do almost all arithmetic operations,
# including addition, subtraction, multiplication, division, and exponentiation.
TOOLS = [
    {
        "name": "calculator",
        "description": "Perform arithmetic operations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Arithmetic expression to evaluate, e.g. '2 + 2 * 3'",
                }
            },
            "required": ["expression"],
        },
    }
]

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def calculate(expression: str) -> str:
    try:
        result = _eval_node(ast.parse(expression, mode="eval").body)
        return str(result)
    except Exception as exc:
        return f"Error: {exc}"


def ask(question: str) -> str:
    messages = [{"role": "user", "content": question}]

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=TOOLS,
        messages=messages,
    )

    while response.stop_reason == "tool_use":
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "calculator":
                result = calculate(block.input["expression"])
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

    return next((block.text for block in response.content if block.type == "text"), "")


if __name__ == "__main__":
    question = input("ask me a math question: ")
    print(ask(question))
