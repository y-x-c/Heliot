from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import subprocess

from placethings.config.common import LinkHelper
from placethings.definition import GnInfo
from placethings.graph_gen.wrapper import graph_gen
from placethings.config.wrapper.config_gen import Config
from placethings.ilp import method
from placethings.netgen.network import DataPlane

log = logging.getLogger()


def init_netsim(topo_device_graph, Gd, G_map, manager_attached_nw_device):
    # get containernet (docker) subnet ip
    # This will be there is containernet is installed, which install the docker
    cmd = (
        "ifconfig | grep -A 1 'docker'"
        " | tail -1 | cut -d ':' -f 2 | cut -d ' ' -f 1")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    docker0_ip = proc.communicate()[0].replace('\n', '')
    log.info("docker0 ip={}".format(docker0_ip))
    # simulate network
    data_plane = DataPlane(topo_device_graph, docker0_ip=docker0_ip)
    # attach manager to a nw device, e.g. 'BB_SWITCH.2'
    data_plane.add_manager(manager_attached_nw_device)
    data_plane.deploy_task(G_map, Gd)
    return data_plane


class ConfigDataHelper(object):

    def __init__(self, cfg, is_export=False):
        assert type(cfg) is Config
        self.cfg = cfg
        self.is_export = is_export
        self.update_id = -1
        # graphs
        self.Gt = None  # Graph for the task
        # We don't use Gn for now. Gn and Gnd looks same in the out

        self.Gn = None  # Graph for the network devices (switch, AP)

        # Gnd is used for mininet creating hosts, switches, and links between.
        # Graph for the network devices + devices (how host is connected to
        #   the swtich)
        self.Gnd = None

        # Gd is used by ILP solver. This has the device connectivity, their
        #   resources and their latency.
        # Graph for the devices (it is fake, virtual graph. To check
        #   connectivity between two devices)
        self.Gd = None

        # Initial Task mapping provided by the user.
        self.G_map = None

        # Task mapping for unassigned tasks from the ILP
        self.result_mapping = None

        # Maximum latency is the longest path between hosts (from sensors to
        #   actuators)
        self.max_latency_log = []

        # Used for debugging, if we change the placement, latency is supposed
        #   to tbe smaller
        self.max_latency_static_log = []

    def init_task_graph(self):
        log.info('init task graph')
        self.Gt = graph_gen.create_task_graph(self.cfg, self.is_export)

    def update_topo_device_graph(self):
        # Creates a new topology:
        # Creating Gn, Gnd and Gd.
        # self.cfg is the input config file, which has data fron
        #   device_data.json, nw_device_data.json and task_data.json
        self.update_id += 1
        log.info('round {}: update topo device graph'.format(self.update_id))
        self.Gn, self.Gnd, self.Gd = graph_gen.create_topo_device_graph(
            self.cfg, self.is_export, export_suffix=self.update_id)

    def update_task_map(self):
        # result_mapping returns the task to the devices
        # G_map is the updated task graph. Tasks, connectivity of tasks and
        #   their attributes (resources, how to invoke)
        G_map, result_mapping = method.place_things(
            self.Gt, self.Gd,
            is_export=self.is_export, export_suffix=self.update_id)
        self.G_map = G_map
        self.result_mapping = result_mapping
        if self.update_id == 0:
            # init update
            self.init_result_mapping = result_mapping
        log.info('mapping result: {}'.format(result_mapping))

    def update_max_latency_log(self):
        max_latency = method.get_max_latency(
            self.Gt, self.Gd, self.result_mapping)
        self.max_latency_log.append(max_latency)
        max_latency_static = method.get_max_latency(
            self.Gt, self.Gd, self.init_result_mapping)
        self.max_latency_static_log.append(max_latency_static)

    def get_max_latency_log(self):
        return self.max_latency_log, self.max_latency_static_log

    def get_graphs(self):
        return self.Gn, self.Gnd, self.Gd, self.G_map

    def _gen_link(src, dst):
        return '{} -> {}'.format

    @staticmethod
    def _update_link_latency(links_dict, n1, n2, latency):
        edge_str = LinkHelper.get_edge(n1, n2)
        latency_before = links_dict[edge_str][GnInfo.LATENCY]
        log.info('update link latency {}: {} => {}'.format(
            edge_str, latency_before, latency))
        # update link latency
        edge_str = LinkHelper.get_edge(n1, n2)
        links_dict[edge_str][GnInfo.LATENCY] = latency
        edge_str = LinkHelper.get_edge(n2, n1)
        links_dict[edge_str][GnInfo.LATENCY] = latency

    @staticmethod
    def _update_link_dst(links_dict, n1, n2, new_n2, new_latency):
        log.info('update link {n1} <-> {n2} => {n1} <-> {new_n2}'.format(
            n1=n1, n2=n2, new_n2=new_n2))
        # delete link
        edge_str = LinkHelper.get_edge(n1, n2)
        del links_dict[edge_str]
        edge_str = LinkHelper.get_edge(n2, n1)
        del links_dict[edge_str]
        # add link
        edge_str = LinkHelper.get_edge(n1, new_n2)
        links_dict[edge_str] = {
            GnInfo.LATENCY: new_latency}
        edge_str = LinkHelper.get_edge(new_n2, n1)
        links_dict[edge_str] = {
            GnInfo.LATENCY: new_latency}

    def update_dev_link_latency(self, dev, nw_dev, latency):
        """
        update device <-> network_dev link latency.
            e.g. change lantency of 'PHONE.0 -> BB_AP.0' from 3ms to 30 ms
        """
        dev_links = self.cfg.all_device_data.device_links.data
        self._update_link_latency(dev_links, dev, nw_dev, latency)

    def update_nw_link_latency(self, nw_dev1, nw_dev2, latency):
        """
        update network_dev <-> network_dev link latency.
            e.g. change lantency of 'BB_SWITCH.0 -> BB_AP.0' from 3ms to 30 ms
        """
        nw_links = self.cfg.all_nw_device_data.nw_device_links.data
        self._update_link_latency(nw_links, nw_dev1, nw_dev2, latency)

    def update_dev_link(self, dev, nw_dev, new_nw_dev, new_latency):
        """
        update device <-> network_dev link.
            e.g. change 'PHONE.0 -> BB_AP.0' to 'PHONE.0 -> BB_AP.1'
        """
        dev_links = self.cfg.all_device_data.device_links.data
        self._update_link_dst(dev_links, dev, nw_dev, new_nw_dev, new_latency)

    def update_nw_link(self, nw_dev1, nw_dev2, new_nw_dev2, new_latency):
        """
        update device <-> network_dev link.
            e.g. change 'PHONE.0 -> BB_AP.0' to 'PHONE.0 -> BB_AP.1'
        """
        nw_links = self.cfg.all_nw_device_data.nw_device_links.data
        self._update_link_dst(
            nw_links, nw_dev1, nw_dev2, new_nw_dev2, new_latency)
