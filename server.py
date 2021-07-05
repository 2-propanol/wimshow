import asyncio
from asyncio.exceptions import TimeoutError
import websockets

from websockets.exceptions import ConnectionClosedOK

MAX_RECEIVERS = 32
MAX_SENDERS = 1
receivers = set()
senders = set()


async def serve_imshow(socket, path) -> None:
    try:
        clientType = await asyncio.wait_for(socket.recv(), 5)
    except TimeoutError:
        await socket.close(1000, "timed out")

    if clientType == "sender":
        if len(senders) < MAX_SENDERS:
            senders.add(socket)
            try:
                while True:
                    image_url = await socket.recv()
                    if receivers:
                        await asyncio.wait(
                            [
                                asyncio.create_task(receiver.send(image_url))
                                for receiver in receivers
                            ]
                        )
            except ConnectionClosedOK:
                pass
            finally:
                senders.remove(socket)
        else:
            socket.close(1000, "senders is full")

    elif clientType == "receiver":
        if len(receivers) < MAX_RECEIVERS:
            receivers.add(socket)
            try:
                while True:
                    response = await socket.recv()
                    if senders:
                        await asyncio.wait(
                            [
                                asyncio.create_task(sender.send(response))
                                for sender in senders
                            ]
                        )
            except ConnectionClosedOK:
                pass
            finally:
                receivers.remove(socket)
        else:
            socket.clone(1000, "receivers is full")
    else:
        await socket.close(1000, "unknown client type")


def start_serve():
    # disableing "Per-Message Deflate"
    start_server = websockets.serve(
        serve_imshow, "0.0.0.0", 9998, compression=None, max_size=8_388_608
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    loop.run_forever()


if __name__ == "__main__":
    start_serve()
