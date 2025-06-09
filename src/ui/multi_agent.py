import os
import asyncio
import re
import subprocess
from dotenv import load_dotenv

from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.agents.strategies.selection.kernel_function_selection_strategy import (
    KernelFunctionSelectionStrategy,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel
from semantic_kernel.functions import KernelFunction
from semantic_kernel.contents.chat_history import ChatHistory

load_dotenv()
chat_history = ChatHistory()

class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""
 
    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        """Condition -  Terminate when User returns "APPROVED" in the chat_history"""
        print(f"Agent - {agent} checking history {history}")
        for message in history:
            if message.role == AuthorRole.USER and "APPROVED" in message.content.upper():
                print("Termination condition met: APPROVED by user.")
                return True
        return False

def extract_html_code(history):
    for message in history:
        if message.role == AuthorRole.ASSISTANT and "```html" in message.content:
            match = re.search(r"```html\s*(.*?)\s*```", message.content, re.DOTALL)
            if match:
                return match.group(1)
    return None


def save_code_to_file(code, filename="index.html"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Saved HTML code to {filename}")


def push_to_github():
    env = {
        **os.environ,
        "GITHUB_USERNAME": os.environ["GITHUB_USERNAME"],
        "GITHUB_PAT": os.environ["GITHUB_PAT"],
        "GITHUB_REPO_URL": os.environ["GITHUB_REPO_URL"],
        "GITHUB_USER_EMAIL": os.environ["GITHUB_USER_EMAIL"],
    }
    subprocess.run(
        ["C:\\Program Files\\Git\\git-bash.exe", "push_to_github.sh"], 
        env=env,
        check=True
    )


async def run_multi_agent(input: str):
    """implement the multi-agent system."""

    kernel = Kernel()

    # Set up Azure Chat Completion Service (assumes env vars are set)
    deployment_name = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    api_key = os.environ["AZURE_OPENAI_API_KEY"]
    api_version = os.environ["AZURE_OPENAI_API_VERSION"]

    service = AzureChatCompletion(
        service_id="azure-openai",
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version = api_version
    )

    kernel.add_service(service)

    # Define agents
    business_analyst = ChatCompletionAgent(
        kernel=kernel,
        name="BusinessAnalyst",
        instructions=(
            "You are a Business Analyst. Understand user requirements, create a detailed project plan with requirements and costing. "
            "This plan should guide the Software Engineer and the Product Owner."
        )
    )

    software_engineer = ChatCompletionAgent(
        kernel=kernel,
        name="SoftwareEngineer",
        instructions=(
            "You are a Software Engineer. Create an HTML/JavaScript web app per the Business Analyst's plan. "
            "Share the code with the Product Owner using the format: ```html [code] ```. Ask clarifying questions if needed."
        )
    )

    product_owner = ChatCompletionAgent(
        kernel=kernel,
        name="ProductOwner",
        instructions=(
            "You are the Product Owner. Verify that the HTML code from the Software Engineer meets all requirements. "
            "Ensure the code is formatted as ```html [code] ```. If everything is complete, reply with 'READY FOR USER APPROVAL'. Otherwise, request fixes."
        )
    )

    # Group Chat setup
    group_chat = AgentGroupChat(
        agents=[business_analyst, software_engineer, product_owner],
        termination_strategy=ApprovalTerminationStrategy()      
    )

    print(f"User input - {input}")
    await group_chat.add_chat_message(input)

    max_turns = 50
    turn_count = 0

    if input.strip().upper() == "APPROVED":
        print("User input is APPROVED. Checking existing context for code extraction.")
        html_code = extract_html_code(chat_history)
        if html_code:
            save_code_to_file(html_code)
            push_to_github()
        else:
            print("No HTML code found to approve.")
        return {
            "messages": [
                {"role": msg.role.name.lower(), "content": msg.content} for msg in chat_history
            ]
        }

    async for content in group_chat.invoke():
        print(f"# {content.name}: {content.content}")
        chat_history.add_message(content)
        turn_count += 1

        if turn_count >= max_turns:
            print("Maximum conversation turns reached. Ending session.")
            break

        if content.role == AuthorRole.ASSISTANT and "READY FOR USER APPROVAL" in content.content.upper():
            print("Approval signal from Product Owner received. Waiting for user approval...")
            break

    return {
        "messages": [
            {
                "role": msg.role.name.lower(),
                "content": msg.content
            } for msg in chat_history
        ]
    }
