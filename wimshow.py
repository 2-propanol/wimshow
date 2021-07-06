import asyncio
import binascii
import json
import subprocess
import sys
import time
from asyncio.exceptions import TimeoutError

import cv2
import websockets
from websockets.exceptions import ConnectionClosedOK


def img_to_uri(image):
    # _, b64_image = cv2.imencode(".bmp", image)
    _, b64_image = cv2.imencode(".png", image, (cv2.IMWRITE_PNG_COMPRESSION, 0))
    # _, b64_image = cv2.imencode(".png", image, ((cv2.IMWRITE_PNG_COMPRESSION, 0, cv2.IMWRITE_PNG_BILEVEL, 1)))
    b64_str_image = binascii.b2a_base64(b64_image).decode("ascii")
    # image_url = f"url(data:image/bmp;base64,{b64_str_image})"
    image_url = f"url(data:image/png;base64,{b64_str_image})"
    return image_url


class WimshowServer:
    def __init__(
        self, host: str = "localhost", port: int = 9998, *, do_serve: bool = True
    ):
        url = f"ws://{host}:{port}"
        self.__process = None
        self.__loop = asyncio.get_event_loop()
        self.__socket = None
        if do_serve:
            self.__process = subprocess.Popen(
                [sys.executable, __file__, "--host", str(host), "--port", str(port)]
            )
        for _ in range(3):
            try:
                self.__socket = self.__loop.run_until_complete(websockets.connect(url))
                self.__loop.run_until_complete(self.__socket.send("sender"))
            except OSError as e:
                if "Errno 61" in str(e):  # Connect call failed
                    time.sleep(1)
                else:
                    raise
            else:
                break
        if not self.__socket:
            raise ConnectionError("failed to connect server")

    @property
    def shape(self):
        self.__loop.run_until_complete(self.__socket.send("monitorInfoRequest"))
        shape = json.loads(self.__loop.run_until_complete(self.__socket.recv()))
        return shape["height"], shape["width"], 3

    def imshow(self, image):
        self.__loop.run_until_complete(self.__socket.send(img_to_uri(image)))
        return self.__loop.run_until_complete(self.__socket.recv())

    def __del__(self):
        if self.__socket:
            self.__loop.run_until_complete(self.__socket.close(1000, "closing sender"))
        if self.__process:
            self.__process.terminate()
        self.__loop.close()


MAX_RECEIVERS = 32
MAX_SENDERS = 1
receivers = set()
senders = set()


async def serve_imshow(socket, path) -> None:
    global receivers, senders

    try:
        clientType = await asyncio.wait_for(socket.recv(), 5)
    except TimeoutError:
        await socket.close(1000, "timed out")

    if clientType == "sender":
        if len(senders) >= MAX_SENDERS:
            socket.close(1000, "senders is full")
            return

        senders.add(socket)
        try:
            while True:
                image_url = await socket.recv()
                if not receivers:
                    await socket.send("no receivers")
                    continue
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
            if not receivers:
                return
            await asyncio.wait(
                [
                    asyncio.create_task(receiver.close(1000, "sender closed"))
                    for receiver in receivers
                ]
            )

    elif clientType == "receiver":
        if len(receivers) >= MAX_RECEIVERS:
            socket.clone(1000, "receivers is full")
            return

        receivers.add(socket)
        try:
            while True:
                response = await socket.recv()
                if not senders:
                    continue
                await asyncio.wait(
                    [asyncio.create_task(sender.send(response)) for sender in senders]
                )
        except ConnectionClosedOK:
            pass
        finally:
            receivers.remove(socket)

    else:
        await socket.close(1000, "unknown client type")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9998,
    )
    args = parser.parse_args()

    # disableing "Per-Message Deflate"
    start_server = websockets.serve(
        serve_imshow, args.host, args.port, compression=None, max_size=8_388_608
    )
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_server)
        loop.run_forever()
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"address `ws://{args.host}:{args.port}` already in use")
        else:
            raise
