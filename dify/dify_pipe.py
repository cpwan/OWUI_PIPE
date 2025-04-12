"""
title: Dify Pipeline+
author: cpwan
version: 0.0.6+
description:
    Added status streaming and citations
"""

"""
title: Dify Pipeline
author: TeddyNote
author_url: https://github.com/teddylee777
funding_url: https://www.buymeacoffee.com/teddylee777
version: 0.0.6
description:
    Dify Pipe for OpenWebUI.
    host_url: 'https://api.dify.ai' or 'http://host.docker.internal'
    dify_api_key: YOUR APP API KEY
    dify_type: 'workflow', 'agent', 'chat', 'completion'
    response_mode: 'streaming' or 'blocking'
    verify_ssl: 'true' if you use dify cloud, 'false' if you use dify docker container(local)
"""
from typing import Optional, Callable, Awaitable, Union, Generator, Iterator, Dict
from pprint import pprint
import requests, json
from dataclasses import dataclass
from typing import Dict, Optional
from pydantic import BaseModel
import os
import time


@dataclass
class DifySchema:
    """
    Data class defining the schema required for Dify API requests

    Attributes:
        dify_type (str): API request type ('workflow', 'agent', 'chat', 'completion')
        user_input_key (str): Key for user input value
        response_mode (str): Response mode ('streaming' or 'blocking')
        user (str): User identifier
    """

    dify_type: str
    user_input_key: str
    response_mode: str
    user: str = ""

    def get_schema(self) -> Dict:
        """
        Returns schema for API request in dictionary format

        Returns:
            Dict: API request schema
        """
        # Return appropriate schema based on API request type
        if self.dify_type == "workflow":
            return {
                "inputs": {},
                "response_mode": self.response_mode,
                "user": self.user,
            }
        elif self.dify_type == "agent":
            return {
                "inputs": {},
                "query": self.user_input_key,
                "response_mode": self.response_mode,
                "user": self.user,
            }
        elif self.dify_type == "chat":
            return {
                "inputs": {},
                "query": "",
                "response_mode": self.response_mode,
                "user": self.user,
            }
        elif self.dify_type == "completion":
            return {
                "inputs": {},
                "response_mode": self.response_mode,
                "user": self.user,
            }
        else:
            raise ValueError(
                "Invalid dify_type. Must be 'completion', 'workflow', 'agent', or 'chat'"
            )


class Pipe:
    """
    Pipe class for interacting with Dify API

    Processes API requests and returns responses in streaming or blocking mode
    """

    class Valves(BaseModel):
        """
        Inner class for storing pipeline configuration values

        Attributes:
            HOST_URL (str): Dify API host URL
            DIFY_API_KEY (str): API authentication key
            USER_INPUT_KEY (str): User input value key
            USER_INPUTS (str): Additional user input values
            DIFY_TYPE (str): API request type
            RESPONSE_MODE (str): Response mode (default: 'streaming')
            VERIFY_SSL (bool): SSL verification flag (default: True)
        """

        HOST_URL: str = "https://api.dify.ai"
        DIFY_API_KEY: str
        USER_INPUT_KEY: str = "input"
        USER_INPUTS: str = "{}"
        DIFY_TYPE: str = "workflow"
        RESPONSE_MODE: Optional[str] = "streaming"
        VERIFY_SSL: Optional[bool] = True

    def __init__(self):
        """Initialize pipeline object"""
        self.type = "pipe"
        self.id = "dify_pipeline"
        self.name = "Dify Pipe"
        self.last_emit_time = 0
        self.citation = False  # disable open webui citations

        # Initialize Valves object with configuration values from environment variables
        self.valves = self.Valves(
            **{
                "pipelines": ["*"],
                "HOST_URL": os.getenv("HOST_URL", "http://host.docker.internal"),
                "DIFY_API_KEY": os.getenv("DIFY_API_KEY", "YOUR_DIFY_API_KEY"),
                "USER_INPUT_KEY": os.getenv("USER_INPUT_KEY", "input"),
                "USER_INPUTS": (
                    os.getenv("USER_INPUTS") if os.getenv("USER_INPUTS") else "{}"
                ),
                "DIFY_TYPE": os.getenv("DIFY_TYPE", "workflow"),
                "RESPONSE_MODE": os.getenv("RESPONSE_MODE", "streaming"),
                "VERIFY_SSL": os.getenv("VERIFY_SSL", False),
            }
        )

        # Set initial data schema
        self.data_schema = DifySchema(
            dify_type=self.valves.DIFY_TYPE,
            user_input_key=self.valves.USER_INPUT_KEY,
            response_mode=self.valves.RESPONSE_MODE,
        ).get_schema()

        self.debug = False

    def create_api_url(self):
        """
        Create API request URL

        Returns:
            str: API endpoint URL
        """
        # Generate endpoint URL based on API type
        if self.valves.DIFY_TYPE == "workflow":
            return f"{self.valves.HOST_URL}/v1/workflows/run"
        elif self.valves.DIFY_TYPE == "agent":
            return f"{self.valves.HOST_URL}/v1/chat-messages"
        elif self.valves.DIFY_TYPE == "chat":
            return f"{self.valves.HOST_URL}/v1/chat-messages"
        elif self.valves.DIFY_TYPE == "completion":
            return f"{self.valves.HOST_URL}/v1/completion-messages"
        else:
            raise ValueError(f"Invalid Dify type: {self.valves.DIFY_TYPE}")

    def set_data_schema(self, schema: dict):
        """
        Dynamically set data schema

        Args:
            schema (dict): New data schema
        """
        self.data_schema = schema

    async def on_startup(self):
        """Method called on server startup"""
        print(f"on_startup: {__name__}")
        pass

    async def on_shutdown(self):
        """Method called on server shutdown"""
        print(f"on_shutdown: {__name__}")
        pass

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """
        Pre-process data before OpenAI API request

        Args:
            body (dict): Request body
            user (Optional[dict]): User information

        Returns:
            dict: Processed request body
        """
        print(f"inlet: {__name__}")
        if self.debug:
            print(f"inlet: {__name__} - body:")
            pprint(body)
            print(f"inlet: {__name__} - user:")
            pprint(user)
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """
        Post-process data after OpenAI API response

        Args:
            body (dict): Response body
            user (Optional[dict]): User information

        Returns:
            dict: Processed response body
        """
        print(f"outlet: {__name__}")
        if self.debug:
            print(f"outlet: {__name__} - body:")
            pprint(body)
            print(f"outlet: {__name__} - user:")
            pprint(user)
        return body

    async def emit_citations(
        self,
        sources: list,
        __event_emitter__: Callable[[dict], Awaitable[None]] = None,
    ):
        for source in sources:
            content = source["content"]
            title = source["document_name"]
            dataset_id = source["dataset_id"]
            document_id = source["document_id"]
            score = source.get("score", "NA")
            url = source.get("doc_metadata", {}).get("url", "")
            await __event_emitter__(
                {
                    "type": "citation",
                    "data": {
                        "document": [content],
                        "metadata": [
                            {
                                "source": title,
                                "page": 1234,
                            }
                        ],
                        "source": {
                            "name": title,
                            "url": url,
                        },
                        "distances": [score],
                    },
                }
            )

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Callable[[dict], Awaitable[None]] = None,
        __event_call__: Callable[[dict], Awaitable[dict]] = None,
    ) -> Optional[dict]:
        """
        Process messages by calling Dify API

        Args:
            user_message (str): User message
            model_id (str): Model identifier
            messages (List[dict]): Message list
            body (dict): Request body

        Returns:
            Union[str, Generator, Iterator]: Generator yielding response text or error messages
        """
        await __event_emitter__(
            {
                "type": "status",  # We set the type here
                "data": {
                    "description": "Working on it.",
                    "done": False,
                },
                # Note done is False here indicating we are still emitting statuses
            }
        )
        messages = body.get("messages", [])

        if messages:
            user_message = messages[-1]["content"]

        if self.debug:
            print(f"pipe: {__name__} - received message from user: {user_message}")

        try:
            # Set API request headers
            self.headers = {
                "Authorization": f"Bearer {self.valves.DIFY_API_KEY}",
                "Content-Type": "application/json",
            }

            # Prepare request data
            data = self.data_schema.copy()
            if self.valves.DIFY_TYPE == "workflow":
                data["inputs"][self.valves.USER_INPUT_KEY] = user_message
            elif self.valves.DIFY_TYPE == "agent" or self.valves.DIFY_TYPE == "chat":
                data["query"] = user_message
            elif self.valves.DIFY_TYPE == "completion":
                data["inputs"]["query"] = user_message
            data["user"] = __user__["email"]

            # Process additional user inputs
            if self.valves.USER_INPUTS:
                inputs_dict = json.loads(self.valves.USER_INPUTS)
                data["inputs"].update(inputs_dict)
            print(data)

            # Execute API request
            response = requests.post(
                self.create_api_url(),
                headers=self.headers,
                json=data,
                verify=self.valves.VERIFY_SSL,
                stream=self.valves.RESPONSE_MODE == "streaming",
            )

            if response.status_code != 200:
                yield f"API request failed with status code {response.status_code}: {response.text}"

            # Process streaming or regular response
            if self.valves.RESPONSE_MODE == "streaming":
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        if decoded_line.startswith("data: "):
                            try:
                                data = json.loads(decoded_line.replace("data: ", ""))
                                print(data)
                                if data["event"] == "message_end":
                                    sources = data["metadata"].get(
                                        "retriever_resources", []
                                    )
                                    await self.emit_citations(
                                        sources, __event_emitter__
                                    )
                                    await __event_emitter__(
                                        {
                                            "type": "status",  # We set the type here
                                            "data": {
                                                "description": "Done.",
                                                "done": True,
                                                "hidden": True,
                                            },
                                            # Note done is False here indicating we are still emitting statuses
                                        }
                                    )

                                if data["event"] == "text_chunk":
                                    yield data["data"]["text"]
                                elif (
                                    data["event"] == "agent_message"
                                    or data["event"] == "message"
                                    or data["event"] == "completion"
                                ):
                                    if "answer" in data:
                                        yield data["answer"]
                                    else:
                                        yield data["data"]["text"]
                                elif data["event"] == "workflow_finished":
                                    yield data["data"]["outputs"]["output"]

                            except Exception as e:
                                print(f"\n\n\n\nError parsing line: {decoded_line}")
                                print(e)
                                print("\n\n\n\n")
            else:
                try:
                    response_data = json.loads(response.text)
                    yield response_data
                except json.JSONDecodeError:
                    yield f"Failed to parse JSON response. Raw response: {response.text}"

        except requests.exceptions.RequestException as e:
            yield f"API request failed: {str(e)}"
