import asyncio
import json
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

from pydantic import AnyUrl


class MCPClient:
    def __init__(self):
        self._session: ClientSession | None = None
        self._exit_stack = AsyncExitStack()

    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError(
                "Not connected to MCP server. Call connect_to_server first."
            )
        return self._session

    async def connect_to_server(
        self,
        config_path: str = "mcp.json",
        server_name: str = "uv",
    ):
        config_file = Path(config_path)
        config = json.loads(config_file.read_text())
        server_config = config["mcpServers"][server_name]

        server_params = StdioServerParameters(
            command=server_config["command"],
            args=server_config["args"],
            cwd=server_config.get("cwd"),
            env=None,
        )
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        _stdio, _write = stdio_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(_stdio, _write)
        )
        await self._session.initialize()

    async def list_tools(self) -> list[types.Tool]:
        result = await self.session().list_tools()
        return result.tools

    async def call_tool(
        self, tool_name: str, tool_input: dict
    ) -> types.CallToolResult | None:
        return await self.session().call_tool(tool_name, tool_input)

    async def cleanup(self):
        await self._exit_stack.aclose()


    async def read_resource(self, uri: str) -> Any:
        result = await self.session().read_resource(AnyUrl(uri))
        resource = result.contents[0]

        if isinstance(resource, types.TextResourceContents):
            if resource.mimeType == "application/json":
                return json.loads(resource.text)

        return resource.text

    async def list_prompts(self) -> list[types.Prompt]:
        result = await self.session().list_prompts()
        return result.prompts

    async def get_prompt(self, prompt_name, args: dict[str, str]):
        result = await self.session().get_prompt(prompt_name, args)
        return result.messages



async def main():
    client = MCPClient()
    await client.connect_to_server()
    try:
        tools = await client.list_tools()
        print(tools)
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())


