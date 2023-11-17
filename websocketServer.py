import asyncio
from websockets.server import serve

async def echo(websocket):
    async for message in websocket:
        print(message)

async def main():
    async with serve(echo, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever

#websocket server to test the client connection from the turn-taking server
if __name__ == "__main__":
    asyncio.run(main())
