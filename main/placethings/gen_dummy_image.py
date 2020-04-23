import base64
import time
import sys
import random
import cStringIO
import threading

import zerorpc
from PIL import Image

mininet_ip=str(sys.argv[1])
port = int(sys.argv[2])
self_id = sys.argv[3]

dummy_image = None
img_id = 0

width, height = 680, 480
resolution = (width, height)
fps = 30

def generate_image():
    global img_id, dummy_image

if __name__ == "__main__":
    client = zerorpc.Client()
    client.connect('tcp://{:s}:{:d}'.format(mininet_ip, port))

    dummy_image = Image.new('RGB', resolution)
    random_grid = map(lambda x: (
        int(random.random() * 256),
        int(random.random() * 256),
        int(random.random() * 256)
    ), [0] * width * height)
    dummy_image.putdata(random_grid)
    img_id += 1

    buf = cStringIO.StringIO()
    dummy_image.save(buf, format="JPEG")
    img_str = base64.b64encode(buf.getvalue())
    img_data = base64.b64encode(img_str)

    while True:
        start_time = time.time()
        data = dict(
            start_time=start_time,
            img_data=img_data,
            img_id=img_id,
            self_id=self_id
        )
        
        result = client.push(data, async=True)
        finish_time = time.time()

        start_sleep = time.time()
        zerorpc.gevent.sleep(1./fps)