import numpy as np
from tqdm import trange

from wimshow import WimshowServer


a = WimshowServer("localhost", 9998)

for _ in trange(120):
    image = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    a.imshow(image)
