import cv2
import binascii
import numpy as np
from tqdm import trange

import asyncio
import websockets


width = 1280
height = 720

def img_to_uri(image):
    # _, b64_image = cv2.imencode(".bmp", image)
    _, b64_image = cv2.imencode(".png", image, (cv2.IMWRITE_PNG_COMPRESSION, 0))
    # _, b64_image = cv2.imencode(".png", image, ((cv2.IMWRITE_PNG_COMPRESSION, 0, cv2.IMWRITE_PNG_BILEVEL, 1)))
    b64_str_image = binascii.b2a_base64(b64_image).decode("ascii")
    # image_url = f"url(data:image/bmp;base64,{b64_str_image})"
    image_url = f"url(data:image/png;base64,{b64_str_image})"
    return image_url

async def imshow(websocket, path) -> None:
    print("net client")

    for _ in trange(120):
        # await websocket.send(img_to_uri(np.random.randint(0,2,(height, width), dtype=np.uint8)))
        await websocket.send(img_to_uri(np.random.randint(0,255,(height, width, 3), dtype=np.uint8)))

        # data = await websocket.recv()
        # print("receive : " + data)

    await asyncio.sleep(3)
    await websocket.close()

# disableing "Per-Message Deflate"
start_server = websockets.serve(imshow, "0.0.0.0", 9998, compression=None)
loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.run_forever()
