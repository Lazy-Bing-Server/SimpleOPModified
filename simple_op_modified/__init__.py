import re
import os
import time
import logging
import types

from typing import Optional
from threading import Lock
from parse import parse
from mcdreforged.api.all import *

from simple_op_modified.constants import LOG_PATH, META, global_server, OP_PREFIX, RESTART_PREFIX
from simple_op_modified.config import config, PlayerExistanceError

restart_lock = Lock()


def tr(key, *fmt) -> str:
    return global_server.tr(f'{META.id}.{key}', *fmt)


def set_file(self: MCDReforgedLogger, file_name: str):
    if self.file_handler is not None:
        self.removeHandler(self.file_handler)
    if not os.path.isfile(file_name):
        with open(file_name, 'w') as f:
            f.write('')
    self.file_handler = logging.FileHandler(file_name, encoding='UTF-8')
    self.file_handler.setFormatter(self.FILE_FMT)
    self.addHandler(self.file_handler)


global_server.logger.set_file = types.MethodType(set_file, global_server.logger)
global_server.logger.set_file(LOG_PATH)


def show_help(source: CommandSource):
    help_message = tr(
        'help_msg', META.name, str(META.version), OP_PREFIX, RESTART_PREFIX
    ).strip().splitlines()
    help_msg_rtext = ''
    for line in help_message:
        if help_msg_rtext != '':
            help_msg_rtext += '\n'
        for PREFIX in [OP_PREFIX, RESTART_PREFIX]:
            result = re.search(r'(?<=§7){}[\S ]*?(?=§)'.format(PREFIX), line)
            if result is not None:
                break
        if result is not None:
            cmd = result.group().strip() + ' '
            help_msg_rtext += RText(line).c(RAction.suggest_command, cmd).h(
                tr("hover.suggest", cmd.strip()))
        else:
            help_msg_rtext += line
    source.reply(help_msg_rtext)


# --------------- Restart ------------------------

@new_thread('SimpleOP - restart')
def restart_confirm(source: CommandSource):
    acq = restart_lock.acquire(blocking=False)
    if not acq:
        for i in range(config.restart_countdown):
            source.get_server().broadcast(RText(tr('text.restart_countdown', config.restart_countdown - i), color=RColor.red))
            time.sleep(1)
        source.get_server().restart()
    else:
        source.reply(no_restart_required(source))
    restart_lock.release()


def restart_unlock(source: CommandSource):
    acq = restart_lock.acquire(blocking=False)
    if not acq:
        restart_already_called(source)
        return
    else:
        if config.restart_need_confirm:
            confirm = RESTART_PREFIX + ' confirm'
            abort = RESTART_PREFIX + ' abort'
            text = tr('text.request_restart').split('/')
            source.get_server().broadcast(RTextList(
                text[0], RText(confirm, color=RColor.gray).c(RAction.run_command, confirm).h(tr('hover.run', confirm)),
                text[1], RText(abort, color=RColor.gray).c(RAction.run_command, abort).h(tr('hover.run', abort)),
                text[2]
                )
            )
        else:
            restart_confirm(source)


def restart_abort(source: CommandSource):
    if restart_lock.locked():
        restart_lock.release()
        source.reply(tr('text.restart_aborted'))
    else:
        no_restart_required(source)


def no_restart_required(source: CommandSource):
    source.reply(tr('error.no_restart_called'))


def restart_already_called(source: CommandSource):
    source.reply(tr('error.restart_already_called'))


# -------------- OP ----------------


def give_op(source: CommandSource):
    if isinstance(source, PlayerCommandSource):
        source.get_server().execute('op {}'.format(source.player))
    else:
        console_runtime_call_error(source)


def convert_source(source: CommandSource):
    if isinstance(source, PlayerCommandSource):
        return source.player
    else:
        return None


def enable_auto(source: CommandSource, players: str = None):
    disable_auto(source, players, reverse=True)


def disable_auto(source: CommandSource, players: Optional[str] = None, reverse=False):
    players = [convert_source(source)] if players is None else players.split(' ')
    if players is None:
        console_runtime_call_error(source)
    else:
        failed, succeed = [], 0
        for p in players:
            try:
                if reverse:
                    config.set_player_auto(p)
                else:
                    config.set_player_manual(p)
            except PlayerExistanceError as e:
                failed.append(e.player)
            else:
                succeed += 1
        failed_text = '' if len(failed) == 0 else tr('text.manual_failed', len(failed), '§r, §e'.join(failed))
        succeed_text = tr('text.manual_succeed', succeed)
        source.reply(succeed_text + failed_text)


def on_info(server: PluginServerInterface, info: Info):
    player = parse_join_info(server, info)
    if info.is_from_server:
        if config.auto_op and player:
            server.execute('op {}'.format(player))


def parse_join_info(server: PluginServerInterface, info: Info) -> Optional[str]:
    parsed = parse('{name}[{player_ip}] logged in with entity id {} at ({})', info.content)
    if parsed is not None and parsed['player_ip'] != 'local':
        if parsed['name'] not in config.manual_list and server.get_permission_level(
                parsed['name']) > config.get_op_permission:
            return parsed['name']
    return None


def switch_auto_op(source: CommandSource, value=None):
    color = {'true': " §a", 'false': ' §c'}
    if value is None:
        value = str(config.auto_op).lower()
        source.reply(tr('text.auto_op_set') + color[value] + value)
        return
    value = value.lower()
    if value in ['true', 'false']:
        target = True if value == 'true' else False
    else:
        cmd_error(source)
        return
    config.auto_op = target
    config.save()
    value = color[value] + value + '§r'
    source.reply(tr('text.auto_op_set') + value)


def console_runtime_call_error(source):
    source.reply(tr('error.runtime'))


def cmd_error(source: CommandSource):
    source.reply(tr('error.cmd_error'))


def on_load(server: PluginServerInterface, prev):
    global restart_lock
    if prev is not None:
        restart_lock = prev.restart_lock

    def pliteral(*literal: str, key: str):
        return Literal(list(literal)).requires(
            lambda src: src.has_permission(config.get(key, 0)),
            failure_message_getter=lambda: tr('error.perm_denied')
        )

    server.register_help_message(OP_PREFIX, tr('op_help_msg'))
    server.register_help_message(RESTART_PREFIX, tr('restart_help_msg'))
    server.register_command(
        pliteral(OP_PREFIX, key='get_op_permission').on_child_error(CommandError, handler=cmd_error, handled=True
                                                                    ).runs(give_op).then(
            Literal('help').runs(show_help)).then(
            Literal('enable').runs(lambda src: enable_auto(src)).then(
                GreedyText('players').runs(lambda src, ctx: enable_auto(src, ctx['players'])))).then(
            Literal('disable').runs(lambda src: disable_auto(src)).then(
                GreedyText('players').runs(lambda src, ctx: disable_auto(src, ctx['players'])))).then(
            Literal('auto').runs(lambda src: switch_auto_op(src)).then(
                QuotableText('value').runs(lambda src, ctx: switch_auto_op(src, ctx['value'])))
        )
    )
    server.register_command(
        Literal(RESTART_PREFIX).on_child_error(CommandError, handler=cmd_error, handled=True
                                               ).runs(restart_unlock).then(
            pliteral('confirm', key='restart_permission').runs(restart_confirm)).then(
            Literal('abort').runs(restart_abort))
        )
