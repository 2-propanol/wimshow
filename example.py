import numpy as np
from tqdm import trange
import time

from wimshow import WimshowServer


a = WimshowServer("localhost", 9998)
time.sleep(6)
shape = a.shape
print(shape)

for _ in trange(60):
    image = np.random.randint(0, 255, shape, dtype=np.uint8)
    # image = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    a.imshow(image)
