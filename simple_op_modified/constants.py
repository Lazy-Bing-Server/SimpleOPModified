from mcdreforged.api.types import ServerInterface


CONFIG_PATH = 'config/SimpleOPModified.json'

global_server = ServerInterface.get_instance().as_plugin_server_interface()

META = global_server.get_plugin_metadata('simple_op_modified')

LOG_PATH = 'logs/SimpleOPModified.json'

OP_PREFIX = '!!op'
RESTART_PREFIX = '!!restart'
