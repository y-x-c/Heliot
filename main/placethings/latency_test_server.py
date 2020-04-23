from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import zerorpc
import base64
import logging
import io
import subprocess
import time

from PIL import Image

from placethings.demo.entity import task as BaseTask
from placethings.demo.entity.base_client import ClientGen
from placethings.utils.common_utils import update_rootlogger


update_rootlogger(level=logging.INFO)

log = logging.getLogger()

fps = 100
inference_latency = 1./fps

class InferenceServer(object):
    def push(self, data):
        sent_time = data['start_time']
        latency_trans = time.time() - sent_time

        start_time = time.time()
        time.sleep(inference_latency)

        latency_comp = time.time() - start_time

        print(sent_time, latency_trans, latency_comp, data['img_id'], data['self_id'])

        return 'done'

server = zerorpc.Server(InferenceServer())
server.bind('tcp://0.0.0.0:18800')
server.run()

