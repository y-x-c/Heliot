from placethings.config.wrapper.task_gen import AllTaskData
from placethings.config.wrapper.config_gen import Config

# all_task = AllTaskData(filepath='sample_configs/config_basic/task_data.json')
config = Config(folderpath='sample_configs/config_basic')

all_task = config.all_task_data
all_nw = config.all_nw_device_data
n_camera = 5

for camera_id in range(2, n_camera):
    all_task.add_task(
        'task_camera{:d}'.format(camera_id),
        exec_cmd = {"default": "cd /opt/github/placethings && python gen_dummy_image.py {next_ip} {next_port} &> /dev/null &"}
    )
    all_task.add_link(src='task_camera{:d}'.format(camera_id), dst='task_findObject', traffic=83886080)
    all_task.add_mapping(
        task='task_camera{:d}'.format(camera_id),
        device='CAMERA.{:d}'.format(camera_id),
        device_list=['CAMERA.{:d}'.format(camera_id)]
    )
    config.add_dev_link('CAMERA.{:d}'.format(camera_id), 'BB_AP.0', 30)

config.export_data(folderpath='sample_configs/config_basic_5')

