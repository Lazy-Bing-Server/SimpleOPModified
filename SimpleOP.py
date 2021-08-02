import time
from threading import Lock
from parse import parse

from mcdreforged.api.all import *

PLUGIN_METADATA = {
	'id': 'simple_op_modified',
	'version': '3',
	'name': 'Simple OP Modified',
	'description': '!!op to get op, !!restart to restart the server',
	'author': {
	'Fallen_Breath',
	'Ra1ny_Yuki'
	},
	'link': 'https://github.com/MCDReforged/SimpleOP',
	'dependencies':
	{
		'mcdreforged': '>=1.0.0',
		'lbs_general_api': '>=1'
		}
}

RESTART_PERMISSION_LEVEL = 1
GET_OP_PERMISSION_LEVEL = 3
ELEVATE_ON_JOIN = False
restart_lock = Lock()
no_auto_list = list()


@new_thread(PLUGIN_METADATA['name'] + ' - restart')
def restart_confirm(source: CommandSource):
	acq = restart_lock.acquire(blocking=False)
	if not acq:
		for i in range(5):
			source.get_server().say(RText('{} 秒后重启服务器!'.format(5 - i), color=RColor.red))
			time.sleep(1)
		source.get_server().restart()
	else:
		source.reply('没有要求重启啊rue')
	restart_lock.release()

def restart_unlock(source: CommandSource):
	acq = restart_lock.acquire(blocking=False)
	if not acq:
		source.reply('已经在重启了rue')
		return
	else:
		api.show(source, api.ezclick('已要求重启，使用§7!!restart confirm§r确认重启(一旦确认无法取消)，使用§7!!restart abort§r取消', '!!restart'), broadcast = True)

def restart_abort(source: CommandSource):
	try:
		restart_lock.release()
		source.reply('成功取消重启')
	except:
		source.reply('没有要求重启啊rue')

def give_op(source: CommandSource):
	if isinstance(source, PlayerCommandSource):
		source.get_server().execute('op {}'.format(source.player))

def on_player_joined(server: ServerInterface, player_name: str, info: Info):
	if server.get_permission_level(player_name) >= GET_OP_PERMISSION_LEVEL and ELEVATE_ON_JOIN:
		server.execute('op {}'.format(player_name))

def parse_join_info(info: Info):
	parsed = parse('{name}[{player_ip}] logged in with entity id {} at ({})', info.content)
	ret = None
	if parsed and parsed['player_ip'] != 'local':
		if parsed['name'] not in no_auto_list and info.get_server().get_permission_level(parsed['name']) > GET_OP_PERMISSION_LEVEL:
			ret = parsed['name']
	return ret

def convert_source(source: CommandSource):
	if isinstance(source, PlayerCommandSource):
		return source.player
	else:
		return None

def enable_auto(source: CommandSource, player = None):
	if player is None:
		player = convert_source(source)
	if player not in no_auto_list and player is not None:
		source.reply('本来就会自动给这玩家op啊rue')
	elif player is None:
		source.reply('没输入有效的玩家名称啊rue')
	else:
		no_auto_list.pop(player)
		source.reply(f'现在玩家§b{player}§r加入时§a会§r被自动授予op权限了')

def disable_auto(source: CommandSource, player = None):
	if player is None:
		player = convert_source(source)
	elif player in no_auto_list and player is not None:
		source.reply('这玩家本来就不会被自动授予op啊rue')
	elif player is None:
		source.reply('没输入有效的玩家名称啊rue')
	else:
		no_auto_list.append(player)
		source.reply(f'现在玩家§b{player}§r加入时§c不会§r被自动授予op权限了')
	
def on_info(server: ServerInterface, info: Info):
	player = parse_join_info(info)
	if info.is_from_server:
		if ELEVATE_ON_JOIN and player:
			server.execute('op {}'.format(player))

def on_load(server: ServerInterface, prev):
	global api, restart_lock, no_auto_list
	api = server.get_plugin_instance('lbs_general_api')
	if prev is not None:
		restart_lock = prev.restart_lock
		no_auto_list = prev.no_auto_list

	server.register_help_message('!!op', '给我op')
	server.register_help_message('!!restart', '重启服务器，延迟5秒')
	server.register_command(
		Literal('!!op').requires(lambda src: src.has_permission(GET_OP_PERMISSION_LEVEL), failure_message_getter=lambda: '权限不足，你想桃子呢').runs(give_op).
		then(Literal('enable').runs(lambda src: enable_auto(src)).
			then(QuotableText('player').runs(lambda src, ctx: enable_auto(src, ctx['player'])))).
		then(Literal('disable').runs(lambda src: disable_auto(src)).
			then(QuotableText('player').runs(lambda src, ctx: disable_auto(src, ctx['player']))))
		)
	server.register_command(
		Literal('!!restart').runs(restart_unlock).
		then(Literal('confirm').requires(lambda src: src.has_permission(RESTART_PERMISSION_LEVEL), failure_message_getter=lambda: '权限不足，你想桃子呢').runs(restart_confirm)).
		then(Literal('abort').runs(restart_abort))
		)
