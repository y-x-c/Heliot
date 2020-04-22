import msgpackrpc
import base64
import time
import sys
import random

from PIL import Image

import base64
import cStringIO

if __name__ == "__main__":
    mininet_ip=str(sys.argv[1])
    port = int(sys.argv[2])

    width, height = 680, 480
    resolution = (width, height)
    fps = 30

    dummy_image = Image.new('RGB', resolution)
    random_grid = map(lambda x: (
        int(random.random() * 256),
        int(random.random() * 256),
        int(random.random() * 256)
    ), [0] * width * height)
    dummy_image.putdata(random_grid)


    while True:
        buf = cStringIO.StringIO()
        dummy_image.save(buf, format="JPEG")
        img_str = base64.b64encode(buf.getvalue())
        img_data = base64.b64encode(img_str)
        
        data = dict(
            start_time=time.time(),
            img_data=img_data,
        )
        
        try:
            client = msgpackrpc.Client(msgpackrpc.Address(mininet_ip, port))
            result = client.call('push', data, time.time())
            print(result)
        except Exception:
            pass

        time.sleep(1/fps)