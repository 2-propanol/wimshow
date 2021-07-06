import time
from io import BytesIO

import cv2
import numpy as np
import png
from tqdm import trange
from simplejpeg import encode_jpeg

from wimshow import WimshowServer

FPS_LIMIT = 60
ideal_interval = 1 / FPS_LIMIT


if __name__ == "__main__":
    a = WimshowServer("localhost", 9998)

    while True:
        shapes = a.shapes
        disps = [f"{shape[1]}x{shape[0]}" for shape in shapes]
        print(f"{len(shapes)} receivers found: {disps}")
        key = input("[c] to continue, others to refresh: ")
        if key == "c":
            break

    shape = shapes[0]

    print("RGB-colored image using PyPNG(pure Python)")
    with trange(120) as t:
        for _ in t:
            start = time.time()
            image = np.random.randint(0, 255, (shape[0], shape[1], 3), dtype=np.uint8)
            a.imshow(image)
            proc_time = time.time() - start
            t.set_postfix(time=f"{proc_time*1000:6.1f}ms")
            if proc_time < ideal_interval:
                time.sleep(ideal_interval - proc_time)

    print("RGB-colored image using cv2(libpng)")
    with trange(120) as t:
        for _ in t:
            start = time.time()
            image = np.random.randint(0, 255, (shape[0], shape[1], 3), dtype=np.uint8)
            _, image_bytes = cv2.imencode(
                ".png", image, (cv2.IMWRITE_PNG_COMPRESSION, 0)
            )
            a.imshow_bytes(image_bytes)
            proc_time = time.time() - start
            t.set_postfix(time=f"{proc_time*1000:6.1f}ms")
            if proc_time < ideal_interval:
                time.sleep(ideal_interval - proc_time)

    print("grayscaled image using PyPNG(pure Python)")
    with trange(120) as t:
        for _ in t:
            start = time.time()
            image = np.random.randint(0, 255, (shape[0], shape[1]), dtype=np.uint8)
            a.imshow(image)
            proc_time = time.time() - start
            t.set_postfix(time=f"{proc_time*1000:6.1f}ms")
            if proc_time < ideal_interval:
                time.sleep(ideal_interval - proc_time)

    print("grayscaled image using cv2(libpng)")
    with trange(120) as t:
        for _ in t:
            start = time.time()
            image = np.random.randint(0, 255, (shape[0], shape[1]), dtype=np.uint8)
            _, image_bytes = cv2.imencode(
                ".png", image, (cv2.IMWRITE_PNG_COMPRESSION, 0)
            )
            a.imshow_bytes(image_bytes)
            proc_time = time.time() - start
            t.set_postfix(time=f"{proc_time*1000:6.1f}ms")
            if proc_time < ideal_interval:
                time.sleep(ideal_interval - proc_time)

    print("binary image using PyPNG with (8-bit encode)")
    with trange(120) as t:
        for _ in t:
            start = time.time()
            image = np.random.randint(0, 2, (shape[0], shape[1]), dtype=np.uint8) * 255
            a.imshow(image)
            proc_time = time.time() - start
            t.set_postfix(time=f"{proc_time*1000:6.1f}ms")
            if proc_time < ideal_interval:
                time.sleep(ideal_interval - proc_time)

    # 1-bit PNG encoding with PyPNG is about 1.7 times slower than 8-bit that.
    # see also: https://pypng.readthedocs.io/en/latest/tr20091230.html#repacking
    print("binary image using PyPNG with (1-bit encode)")
    with trange(120) as t:
        for _ in t:
            start = time.time()
            image = np.random.randint(0, 2, (shape[0], shape[1]), dtype=np.bool8)
            with BytesIO() as bs:
                png.from_array(
                    image.reshape(image.shape[0], -1),
                    mode="L;1",
                    info={"compression": 0},
                ).write(bs)
                a.imshow_bytes(bs.getvalue())
            proc_time = time.time() - start
            t.set_postfix(time=f"{proc_time*1000:6.1f}ms")
            if proc_time < ideal_interval:
                time.sleep(ideal_interval - proc_time)

    print("binary image using cv2(libpng)")
    with trange(120) as t:
        for _ in t:
            start = time.time()
            image = np.random.randint(0, 2, (shape[0], shape[1]), dtype=np.uint8) * 255
            _, image_bytes = cv2.imencode(
                ".png",
                image,
                (cv2.IMWRITE_PNG_COMPRESSION, 0, cv2.IMWRITE_PNG_BILEVEL, 1),
            )
            a.imshow_bytes(image_bytes)
            proc_time = time.time() - start
            t.set_postfix(time=f"{proc_time*1000:6.1f}ms")
            if proc_time < ideal_interval:
                time.sleep(ideal_interval - proc_time)

    print("lossy RGB-colored image using cv2(libjpeg)")
    with trange(120) as t:
        for _ in t:
            start = time.time()
            image = np.random.randint(0, 255, (shape[0], shape[1], 3), dtype=np.uint8)
            _, image_bytes = cv2.imencode(
                ".jpg",
                image,
                (cv2.IMWRITE_JPEG_QUALITY, 95, cv2.IMWRITE_JPEG_OPTIMIZE, 1),
            )
            a.imshow_bytes(image_bytes)
            proc_time = time.time() - start
            t.set_postfix(time=f"{proc_time*1000:6.1f}ms")
            if proc_time < ideal_interval:
                time.sleep(ideal_interval - proc_time)

    print("lossy RGB-colored image using simplejpeg(libjpeg-turbo)")
    with trange(120) as t:
        for _ in t:
            start = time.time()
            image = np.random.randint(0, 255, (shape[0], shape[1], 3), dtype=np.uint8)
            image_bytes = encode_jpeg(image, quality=95, colorsubsampling="422")
            a.imshow_bytes(image_bytes)
            proc_time = time.time() - start
            t.set_postfix(time=f"{proc_time*1000:6.1f}ms")
            if proc_time < ideal_interval:
                time.sleep(ideal_interval - proc_time)

