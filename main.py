import asyncio
import os

from anthropic import Anthropic

from dotenv import load_dotenv

from mcp_client import MCPClient

load_dotenv()
client = Anthropic()  


class MCPChatBot:
    def __init__(self):
        self.mcp_client = MCPClient()
        self.anthropic = Anthropic() 
      
        self.available_tools: list[dict] = []

    async def connect(self):
        await self.mcp_client.connect_to_server()
        tools = await self.mcp_client.list_tools()
        self.available_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in tools
        ]

    async def process_query(self, query: str):
        if query.startswith("@"):
            doc_id = query[1:].split()[0]
            doc_content = await self.mcp_client.read_resource(f"docs://documents/{doc_id}")
            query = f"<document id='{doc_id}'>\n{doc_content}\n</document>\n\n{query[len(doc_id) + 1:].strip()}"

        messages = [{"role": "user", "content": query}]

        while True:
            response = self.anthropic.messages.create(
                model="claude-sonnet-5",
                max_tokens=1024,
                messages=messages,
                tools=self.available_tools,
            )

            assistant_content = []
            has_tool_use = False

            for content in response.content:
                if content.type == "text":
                    print(content.text)
                    assistant_content.append(content)

                elif content.type == "tool_use":
                    has_tool_use = True
                    assistant_content.append(content)

                    tool_name = content.name
                    tool_input = content.input
                    tool_id = content.id

                    print(f"\n[Calling tool {tool_name} with input {tool_input}]")

                    result = await self.mcp_client.call_tool(tool_name, tool_input)
                    tool_result_text = (
                        result.content[0].text
                        if result and result.content
                        else "No result returned."
                    )

                    messages.append({"role": "assistant", "content": assistant_content})
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": tool_result_text,
                                }
                            ],
                        }
                    )

            if not has_tool_use:
                break

    async def chat_loop(self):
        print("MCP Chatbot Started!")
        print("Type your questions or 'quit' to exit.\n")

        while True:
            try:
                query = input("Query: ").strip()
                if query.lower() == "quit":
                    break
                await self.process_query(query)
                print()
            except Exception as e:
                print(f"\nError: {e}")

    async def cleanup(self):
        await self.mcp_client.cleanup()


async def main():
    chatbot = MCPChatBot()
    try:
        await chatbot.connect()
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

