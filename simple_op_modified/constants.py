import os

from mcdreforged.api.types import ServerInterface

global_server = ServerInterface.get_instance().as_plugin_server_interface()

OLD_CONFIG_PATH = 'config/SimpleOPModified.json'

CONFIG_PATH = os.path.join(global_server.get_data_folder(), 'SimpleOPModified.json')

META = global_server.get_plugin_metadata('simple_op_modified')

LOG_FOLDER = os.path.join(global_server.get_data_folder(), 'logs')
LOG_FILE = 'SimpleOPModified.log'

if not os.path.isdir(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

LOG_PATH = os.path.join(LOG_FOLDER, LOG_FILE)

OP_PREFIX = '!!op'
RESTART_PREFIX = '!!restart'
