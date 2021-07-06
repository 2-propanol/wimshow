import asyncio
import binascii
import json
import subprocess
import sys
import time
from asyncio.exceptions import TimeoutError
from io import BytesIO
from pathlib import Path

import png
import websockets
from websockets.exceptions import ConnectionClosedOK


def img_to_uri(image):
    color_mode = "RGB"
    if image.ndim == 2:
        color_mode = "L"
    with BytesIO() as bs:
        # why reshaping: https://github.com/drj11/pypng/issues/105
        png.from_array(
            image.reshape(image.shape[0], -1), mode=color_mode, info={"compression": 0}
        ).write(bs)
        b64_str_image = binascii.b2a_base64(bs.getvalue()).decode("ascii")
    image_url = f"url(data:image/png;base64,{b64_str_image})"
    return image_url


def bytes_to_uri(image_bytes, filetype="png"):
    b64_str_image = binascii.b2a_base64(image_bytes).decode("ascii")
    image_url = f"url(data:image/{filetype};base64,{b64_str_image})"
    return image_url


class WimshowServer:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 9998,
        *,
        ws_serve: bool = True,
        httpd_serve: bool = False,
    ):
        url = f"ws://{host}:{port}"
        self.__ws_process = None
        self.__httpd_process = None
        self.__loop = asyncio.get_event_loop()
        self.__socket = None
        if ws_serve:
            self.__ws_process = subprocess.Popen(
                [sys.executable, __file__, "--host", str(host), "--port", str(port)]
            )
        dist_dir = Path(__file__).parent.joinpath("dist")
        if port == 9998:
            print(f"local access: file://{dist_dir}/index.html")
        else:
            print(f"local access: file://{dist_dir}/index.html?SocketUrl={url}")
        if httpd_serve:
            self.__httpd_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "http.server",
                    str(port + 1),
                    "--bind",
                    str(host),
                    "--directory",
                    str(dist_dir),
                ]
            )
            print(f"remote access: http://{host}:{port+1}/index.html?SocketUrl={url}")
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
    def shapes(self):
        self.__loop.run_until_complete(self.__socket.send("monitorInfoRequest"))
        num_receivers = int(self.__loop.run_until_complete(self.__socket.recv()))
        dicts = [
            json.loads(self.__loop.run_until_complete(self.__socket.recv()))
            for _ in range(num_receivers)
        ]
        return [(d["height"], d["width"], 3) for d in dicts]

    def imshow(self, image):
        self.__loop.run_until_complete(self.__socket.send(img_to_uri(image)))
        num_receivers = int(self.__loop.run_until_complete(self.__socket.recv()))
        return [
            self.__loop.run_until_complete(self.__socket.recv())
            for _ in range(num_receivers)
        ]

    def imshow_bytes(self, image_bytes, filetype="png"):
        self.__loop.run_until_complete(
            self.__socket.send(bytes_to_uri(image_bytes, filetype))
        )
        num_receivers = int(self.__loop.run_until_complete(self.__socket.recv()))
        return [
            self.__loop.run_until_complete(self.__socket.recv())
            for _ in range(num_receivers)
        ]

    def __del__(self):
        if self.__socket:
            self.__loop.run_until_complete(self.__socket.close(1000, "closing sender"))
        if self.__ws_process:
            self.__ws_process.terminate()
        if self.__httpd_process:
            self.__httpd_process.terminate()
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
                await socket.send(str(len(receivers)))
                if not receivers:
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
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=9998)
    parser.add_argument(
        "--use_deflate", action="store_true", help="use Per-Message Deflate"
    )
    args = parser.parse_args()

    compress = None
    if args.use_deflate:
        compress = "deflate"
    # disableing "Per-Message Deflate"
    start_server = websockets.serve(
        serve_imshow, args.host, args.port, compression=compress, max_size=8_388_608
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
