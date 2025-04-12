"""
title: n8n Pipe Function
author: Cole Medin
author_url: https://www.youtube.com/@ColeMedin
version: 0.2.0

This module defines a Pipe class that utilizes N8N for an Agent
"""

from typing import Optional, Callable, Awaitable
from pydantic import BaseModel, Field
import os
import time
import requests
import asyncio, aiohttp


def extract_event_info(event_emitter) -> tuple[Optional[str], Optional[str]]:
    if not event_emitter or not event_emitter.__closure__:
        return None, None
    for cell in event_emitter.__closure__:
        if isinstance(request_info := cell.cell_contents, dict):
            chat_id = request_info.get("chat_id")
            message_id = request_info.get("message_id")
            return chat_id, message_id
    return None, None


class Pipe:
    class Valves(BaseModel):
        n8n_url: str = Field(default="http://n8n:5678/webhook/wiki-pipe")
        n8n_bearer_token: str = Field(default="...")
        input_field: str = Field(default="chatInput")
        response_field: str = Field(default="output")

    def __init__(self):
        self.type = "pipe"
        self.id = "n8n_pipe"
        self.name = "N8N Pipe"
        self.valves = self.Valves()
        self.last_emit_time = 0

    async def emit_citations(
        self,
        intermediateSteps: list,
        __event_emitter__: Callable[[dict], Awaitable[None]] = None,
    ):
        print(intermediateSteps)
        for step in intermediateSteps:
            content = step["observation"]
            action = step["action"]
            tool = action["tool"]
            tool_input = action["toolInput"]
            print(content)
            print(action)
            await __event_emitter__(
                {
                    "type": "citation",
                    "data": {
                        "document": [content],
                        "source": {
                            "name": f"{tool}:{tool_input}",
                        },
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
        await __event_emitter__(
            {
                "type": "status",
                "data": {
                    "description": "Running n8n workflow.",
                    "done": False,
                    "hidden": False,
                },
            }
        )
        chat_id, _ = extract_event_info(__event_emitter__)
        messages = body.get("messages", [])

        # Verify a message is available
        if messages:
            question = messages[-1]["content"]
            try:
                # Invoke N8N workflow
                headers = {
                    "Authorization": f"Bearer {self.valves.n8n_bearer_token}",
                    "Content-Type": "application/json",
                }
                payload = {"sessionId": f"{chat_id}"}
                payload[self.valves.input_field] = question

                n8n_response = {}
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.valves.n8n_url, json=payload, headers=headers
                    ) as response:
                        if response.status == 200:
                            n8n_response = await response.json()
                            answer = n8n_response[self.valves.response_field]

                        else:
                            raise Exception(
                                f"Error: {response.status} - {await response.text()}"
                            )
                print(n8n_response)
                print(n8n_response.get("intermediateSteps", {}))
                try:
                    await self.emit_citations(
                        n8n_response.get("intermediateSteps", {}), __event_emitter__
                    )
                except Exception as e:
                    print("Error: ", e)
            except Exception as e:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Error during execution.",
                            "done": False,
                        },
                    }
                )
                yield {"error": str(e)}
        # If no message is available alert user
        else:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Error: No messages found in the request body",
                        "done": False,
                    },
                }
            )
            body["messages"].append(
                {
                    "role": "assistant",
                    "content": "No messages found in the request body",
                }
            )

        await __event_emitter__(
            {
                "type": "status",
                "data": {
                    "description": "n8n workflow execution completed",
                    "done": True,
                },
            }
        )
        yield answer
