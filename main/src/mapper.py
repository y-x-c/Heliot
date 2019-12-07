"""
Maps tasks to their devices & nodes, and assigns port numbers to the tasks.

Basic map Structure:
   map = {
      'task_1': { 
         'in_port': #,                                            # This task's listening port, if any
         'out_ports': { 'task1_data': [#, ...], ... },            # Receiving task's listening ports
         'device': 'device_x',                                    # This task's device
         'out_devices: { 'task1_data': ['device_x', ...], ... },  # Receiving task's device
         'node': 'node_x'                                         # This task's respective node
      },
      'task_2': ...,
      ...,
      'master': 'device_x',                       # Not implemented
      'node_x': { ip: #, device: 'device_x' },    # Not implemented
      'device_x': { ip: },
      ...,
   }
"""

# Imports
from core.device import *
from core.taskHeliot import *
import sys
import json


# Logger
import logging
logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)


class mapper:

   # Port numbers to start incrementing from
   initialOutPort  = 7000
   initialInPort   = 14000


   def __init__(self):
      self.map = {}


   # Returns an outport and increments
   @staticmethod
   def getOutPort():
      outport = mapper.initialOutPort
      mapper.initialOutPort += 1
      return outport

   # Returns an inport and increments
   @staticmethod
   def getInPort():
      inport = mapper.initialInPort
      mapper.initialInPort += 1
      return inport

   
   # Creates the initial map structure for task
   def addTaskMapping(self, _task, _device):
      if self.checkTask(_task) and self.checkDevice(_device):
         inPort = None
         outPorts = {}
         dev = _device._id
         out_devices = {}
         node = ''

         for output in _task._outputids:
               outPorts[output] = []
               out_devices[output] = []

         if len(_task._inputids) != 0:
               inPort = mapper.getInPort()
               
         self.map[_task._taskid] = {
               'in_port': inPort,
               'out_ports': outPorts,
               'device': dev,
               'out_devices': out_devices,
               'node': node
         }


   # Map 'master' to a device
   def addMasterMapping(self, _device):
      if self.checkDevice(_device):
         pass


   # Maps devices to thier ip
   def addDeviceMapping(self, _device):
      if self.checkDevice(_device):
         self.map[_device._id] = { 'ip': _device.get_connection()[0]._attributes['_ip'] }


   # Maps all tasks' 'out_devices' and 'out_ports' based on their _inputids and _outputids in taskHeliot.py
   # Writes the map to a JSON file
   # Thus, should be called last. After all other mapping is done.
   def mapDataflow(self, tasks, devices, nodes, dir):
      print(self.map)
      for task in tasks:
         for input_id in task._inputids:
               for key, value in self.map.items():
                  if 'out_ports' in value and input_id in value['out_ports']:
                     self.map[key]['out_ports'][input_id].append(self.map[task._taskid]['in_port'])
                     self.mapOutDevice(key, input_id, task, devices, nodes)
      
      with open(dir, 'w') as file:
         json.dump(self.map, file, sort_keys=True, indent=4)     
   
   # Helper function of mapDataflow - Creates a map for each task's 'out_devices'
   def mapOutDevice(self, key, input_id, task, devices, nodes):
      for node in nodes:
         if node._id == task._nodeid:
               for device in devices:
                  if device._type == node._type:
                     self.map[key]['out_devices'][input_id].append(device._id)
                           
   
   # Checks if task is of type taskHeliot
   def checkTask(self, _task):
      if type(_task) is taskHeliot:
         return True
      else:
         logger.error("Task mapping must have an argument of type task")
         sys.exit()

   # Checks if device is of type device
   def checkDevice(self, _device):
      if type(_device) is device:
         return True
      else:
         logger.error("Device mapping must have an argument of type device")
         sys.exit()


"""
BEFORE
{ 
   'prince_device':{ 
      'ip':'127.0.0.1'
   },
   'task3':{ 
      'in_ports':8000,
      'out_ports':{ 

      },
      'device':'prince_device',
      'out_devices':{ 

      }
   },
   'task4':{ 
      'in_ports':8001,
      'out_ports':{ 

      },
      'device':'prince_device',
      'out_devices':{ 

      }
   },
   'task1':{ 
      'in_ports':None,
      'out_ports':{ 
         'task1_data':[ 

         ]
      },
      'device':'prince_device',
      'out_devices':{ 
         'task1_data':[ 

         ]
      }
   },
   'task2':{ 
      'in_ports':None,
      'out_ports':{ 
         'task2_data':[ 

         ]
      },
      'device':'prince_device',
      'out_devices':{ 
         'task2_data':[ 

         ]
      }
   }
}
"""


"""
AFTER
{ 
   'prince_device':{ 
      'ip':'127.0.0.1'
   },
   'task3':{ 
      'in_ports':8000,
      'out_ports':{ 

      },
      'device':'prince_device',
      'out_devices':{ 

      }
   },
   'task4':{ 
      'in_ports':8001,
      'out_ports':{ 

      },
      'device':'prince_device',
      'out_devices':{ 

      }
   },
   'task1':{ 
      'in_ports':None,
      'out_ports':{ 
         'task1_data':[ 
            8000,
            8001
         ]
      },
      'device':'prince_device',
      'out_devices':{ 
         'task1_data':[ 
            'prince_device',
            'prince_device'
         ]
      }
   },
   'task2':{ 
      'in_ports':None,
      'out_ports':{ 
         'task2_data':[ 
            8000,
            8001
         ]
      },
      'device':'prince_device',
      'out_devices':{ 
         'task2_data':[ 
            'prince_device',
            'prince_device'
         ]
      }
   }
}
"""
