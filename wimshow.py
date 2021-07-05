import asyncio
import binascii
from multiprocessing import Process

import cv2
import websockets


def img_to_uri(image):
    # _, b64_image = cv2.imencode(".bmp", image)
    _, b64_image = cv2.imencode(".png", image, (cv2.IMWRITE_PNG_COMPRESSION, 0))
    # _, b64_image = cv2.imencode(".png", image, ((cv2.IMWRITE_PNG_COMPRESSION, 0, cv2.IMWRITE_PNG_BILEVEL, 1)))
    b64_str_image = binascii.b2a_base64(b64_image).decode("ascii")
    # image_url = f"url(data:image/bmp;base64,{b64_str_image})"
    image_url = f"url(data:image/png;base64,{b64_str_image})"
    return image_url


class WimshowServer:
    def __init__(self, url: str):
        # self.__process = Process(target=start_serve)
        # self.__process.start()
        self.__loop = asyncio.get_event_loop()
        self.__socket = self.__loop.run_until_complete(websockets.connect(url))
        self.__loop.run_until_complete(self.__socket.send("sender"))

    def imshow(self, image):
        # return self.__loop.run_until_complete(self.__socket.send(image_url))
        self.__loop.run_until_complete(self.__socket.send(img_to_uri(image)))
        return self.__loop.run_until_complete(self.__socket.recv())

    def __del__(self):
        self.__loop.run_until_complete(self.__socket.close(1000, "sender closed"))
        self.__loop.close()
        # self.__process.terminate()
