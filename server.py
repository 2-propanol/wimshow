import cv2
import binascii
import numpy as np
import time

width = 1280
height = 720


def str_to_uri(string):
    image = np.fromfunction(
        lambda y, x, c: 255 * (c == 0)
        + x / width * 255 * (c == 1)
        + y / height * 255 * (c == 2),
        (height, width, 3),
    ).astype(np.uint8)
    cv2.putText(
        image,
        string,
        (width // 4, height // 4 * 3),
        cv2.FONT_HERSHEY_SIMPLEX,
        15,
        (0, 255, 0),
        8,
        cv2.LINE_AA,
    )

    _, b64_image = cv2.imencode(".png", image)
    b64_str_image = binascii.b2a_base64(b64_image).decode("ascii")
    image_url = f"data:image/png;base64,{b64_str_image}"
    return image_url


import asyncio
import websockets


async def accept(websocket, path):
    while True:
        for i in range(10):
            s = time.time()

            # print(f"message sent ({i})")
            await websocket.send(str_to_uri(str(i)))

            data = await websocket.recv()
            # print("receive : " + data)

            f = time.time()
            print(f"\r{1/(f-s):4.1f}fps", end="")


start_server = websockets.serve(accept, "localhost", 9998)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
