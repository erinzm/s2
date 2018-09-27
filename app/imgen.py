from typing import List
from io import BytesIO
import base64
import numpy as np
from PIL import Image

def load_image(fp) -> np.ndarray:
    image = Image.open(fp)
    arr = np.asarray(image)
    maxval = np.iinfo(arr.dtype).max
    arr = arr.astype('float') / maxval
    return arr

def as_base64_png(img: Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format='png')
    data = b'data:image/png;base64,' + base64.encodestring(buf.getvalue())
    return data.decode('utf-8')

def perturb_image(base_image: np.ndarray, weights: np.ndarray, bases: List[np.ndarray]):
    perturbation = np.zeros_like(base_image)
    assert(len(weights) == len(bases))
    assert(all(base_image.shape == base.shape for base in bases))
    
    for i, basis in enumerate(bases):
        perturbation += weights[i] * basis
    
    pimage = base_image + perturbation
    pimage[pimage > 1] = 1
    pimage[pimage < 0] = 0

    return pimage