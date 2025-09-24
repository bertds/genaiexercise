from strands import Agent, tool
from strands_tools import calculator # Import the calculator tool
import argparse
import json
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel
from retrying import retry

app = BedrockAgentCoreApp()

# Create a custom tool 
@tool
def weather():
    """ Get weather """ # Dummy implementation
    return "sunny"


model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"
model = BedrockModel(
    model_id=model_id,
)
agent = Agent(
    model=model,
    tools=[calculator, weather],
    system_prompt="You're a helpful assistant. You can do simple math calculation, and tell the weather.",
    callback_handler=None,  # default is PrintingCallbackHandler
)

# Retry if the agent throws a throttling exception.
# You could also return a response to the client and let it handle the retriable HTTP codes
# using https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/API_InvokeAgentRuntime.html#API_InvokeAgentRuntime_ResponseSyntax
@retry(retry_on_exception=lambda e: ('throttl' in str(e)),
       wait_fixed=5000,
       stop_max_delay=30*1000)
def call_agent(user_input):
    return agent(user_input)

@app.entrypoint
def strands_agent_bedrock(payload):
    """
    Invoke the agent with a payload
    """
    user_input = payload.get("prompt")
    print("User input:", user_input)
    response = call_agent(user_input)
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()
