import json
import os.path
import shutil

from mcdreforged.api.all import Serializable
from typing import List

from simple_op_modified.constants import CONFIG_PATH, global_server, OLD_CONFIG_PATH


class Config(Serializable):
    restart_permission: int = 1
    get_op_permission: int = 3
    auto_op: bool = False
    manual_list: List[str] = []
    restart_need_confirm: bool = True
    restart_countdown: int = 5

    def save(self):
        with open(CONFIG_PATH, 'w') as f:
            json.dump(self.serialize(), f, ensure_ascii=False, indent=4)

    @classmethod
    def load(cls):
        if os.path.isfile(OLD_CONFIG_PATH) and not os.path.isfile(CONFIG_PATH):
            shutil.move(OLD_CONFIG_PATH, CONFIG_PATH)
        return global_server.load_config_simple(
            CONFIG_PATH, in_data_folder=False, default_config=cls.get_default().serialize(), echo_in_console=True,
            target_class=cls
        )

    @property
    def lower_manual_dict(self):
        ret = {}
        for p in self.manual_list:
            ret[p.lower()] = p
        return ret

    def set_player_manual(self, player: str):
        if player.lower() in self.lower_manual_dict.keys():
            raise PlayerExistanceError(player)
        else:
            self.manual_list.append(player)

    def set_player_auto(self, player: str):
        if player.lower() in self.lower_manual_dict.keys():
            self.manual_list.remove(self.lower_manual_dict[player.lower()])
        else:
            raise PlayerExistanceError(player)

    def get(self, key: str, default=None):
        if hasattr(self, key):
            return self.__dict__[key]
        else:
            return default


class PlayerExistanceError(Exception):
    def __init__(self, player: str):
        self.player = player


config = Config.load()
