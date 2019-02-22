"""
The definition of workload in Heliot consists of Testbed and Scenario

Testbed defines the physical devices. The devices are defined in core folder.
Testbed consists of list of devices

"""

"""
Logic and predefined heliot keywords used in the testbed file:

1) device should have unique id. A list of id is maintained and it is ensured each device has unique id
2) Predefined keywords for connection object in device is used to validate the existence of testbed
Keywords: _ssh (_ip)
3) Predefined keywords for operating system is used in order to contact respective devices and do initialization

"""


#Heliot imports
from core.device import *
from utilss.ping import *
from utilss.ssh import *

#Network imports for mininet
from network.netHeliot import *


#other imports
import sys
import logging
import os

####################initialization file path
supported_os=['_ubuntu','_windows','_linux','_android']


logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
ch.setLevel(logging.DEBUG)

logger.addHandler(ch)

logger.setLevel(logging.DEBUG)



class testbed:

# testbed has list of devices
# device attributes  defines the device in more details
# device attributes are: list of compute, memory, list of connection, list of sensors, os and description



    def __init__(self,name=''):
        self._name = name

        # _device store the list of physical devices
        self._device = []

        # Stores the ids of all the devices in the testbed
        # all devices should have unique ids
        self._id = []

    # Add device to the list of devices in the testbed
    def add_device(self, d):
        #verify d is device object
        if type(d) is device:
            id = d._id
            print('Adding device ',id, ' to testbed')
            # check if device of this id is already present in testbed
            if str(id) in self._id:
                logger.error(str(id)+' is already present in testbed')
                logger.error('id of each device should be unique')
                sys.exit()

            self._device.append(d)
            self._id.append(str(id))

        else:
            logger.error('add_device called with wrong input')
            sys.exit()

    # get the list of devices in the current testbed
    def get_device(self):
        return self._device

    def get_info(self):
        return self._name, self._device


# Validation is very important step of testbed in heliot
# We need to ensure all the devices are reachable by heliot_runtime
# Steps:
# 1) We first do ping in case of linux/windows devices. For Android, we try to communicate to the Andoid app running rest api


    def validate(self):

        logger.info('Validating the devices in Testbed')

        #Validate each device in the testbed
        for dev in self._device:

######################################Checking connectivity of all devices first #######################################################
            #In case no connection object is present
            if len(dev.get_connection())==0:
                logger.error('connection object is not known to heliot')
                logger.error(str(dev._id) +'  cannot be reached')
                logger.error('Testbed validation failed')
                sys.exit()

            #connection object of device
            con = dev.get_connection()[0] #At present, there is only one type of connection obect which is ssh/restAPI


            if con._type =='_ssh':
                ip = con._attributes['_ip']

                # Checking the reachability of devices using ping
                val = check_ping(ip=ip)
                if not val:
                    logger.error(str(dev._id) +'  cannot be reached')
                    logger.error('Testbed validation failed')
                    sys.exit()

                logger.info(str(dev._id)+' is connected')

                # After ping, now doing initialize
                username = con._attributes['_username']
                password = con._attributes['_password']


                val = False
                # Based on type of OS (linux/windows/android) different initialization is done
                dev_os = dev.get_os()._type

                if str(dev_os) not in supported_os:
                    logger.error(str(dev_os) +'  is not supported in heliot')
                    logger.error('Testbed validation failed')
                    sys.exit()

                if str(dev_os)=='_ubuntu' or str(dev_os)=='_linux':
                    val = do_intializaton_linux(ip=ip,username=username, password=password, logger = logger)
                    if not val:
                        logger.error(str(dev._id) +'  cannot be initialized')
                        logger.error('Testbed validation failed')
                        sys.exit()

                logger.info('heliot initalization done for '+ str(dev._id))




            else :
                logger.error(str(con._type) +' is not known to heliot')
                logger.error(str(dev._id) +'  validation failed')
                logger.error('Testbed validation failed')
                sys.exit()

        logger.info('Testbed validated')


    def stop_network(self):
        print('Stopping the network');
        self._net._network.stop()

    def set_scenario(self,_scenario=None):
        self._scenario=_scenario
        print('Adding scenario to the testbed')

    def start_network(self):

        # a digit has to be added as part of the id, else
        # mininet is not able to initialize the switches and hosts

        mininet_id="0"

        if os.getuid()!=0:
            logger.error('Heliot cannot start network without sudo privileges')
            logger.error('if using jupyter, use: "sudo jupyter notebook --allow-root"')
            sys.exit()
        else:

            # Note this has to be started on the mininet machine
            # At present, I am assuming my work machine is mininet machine

            self._net = netHeliot()

            #adding the virtual infrastructure nodes
            # virtual switches
            print('Adding infranodes to the network')
            for inode in self._scenario._infranode:
                #print('Adding:',inode._id+mininet_id)
                self._net.add_switch(inode._id+mininet_id)

            print('Adding nodes to the network')
            #Adding other nodes as hosts
            for node in self._scenario._node:
                self._net.add_host(node._id+mininet_id)

            print('Adding airSim sensors to the network')
            for sensor in self._scenario._airsimSensor:
                self._net.add_host(sensor._id+mininet_id)

            #Add the links
            for link in self._scenario._mininetLink:
                self._net.add_link(link._id_1+mininet_id, link._id_2+mininet_id)

            print('Starting the network using Mininet')
            self._net._network.start()
            self._net._network.pingAll()
            #self.net._network.stop()


        # Function to run the tasks on the nodes
        # Testbed object tbed is passed as the input
    def start_tasks(self):

        for task in self._scenario._tasks:
            print('Attempting to start Task:',task._taskid, 'on node:',task._nodeid)

#t1 = testbed('mytestbed')
#print(t1.get_info())
