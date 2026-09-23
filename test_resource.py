import asyncio
from mcp_client import MCPClient


async def main():
    client = MCPClient()
    await client.connect_to_server()
    try:
        # Direct resource — list all doc IDs
        doc_list = await client.read_resource("docs://documents")
        print("docs://documents ->", doc_list)

        # Templated resource — fetch one document's contents
        content = await client.read_resource("docs://documents/report.pdf")
        print("docs://documents/report.pdf ->", content)
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())