import json
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio

import sys
import os
from PIL import Image
from loguru import logger as log
import requests
import time

# Add plugin to sys.paths
sys.path.append(os.path.dirname(__file__))

# Import globals
import globals as gl

# Import own modules
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page

class Counter(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)
        
        self.value = 0

    def on_ready(self):
        settings = self.get_settings()
        if settings.get("restore", True):
            self.value = settings.get("value", 0)

        self.show_value()
        self.key_down_time: int = 0

    def get_config_rows(self) -> list:
        self.restore_switch = Adw.SwitchRow(title=self.plugin_base.lm.get("actions.counter.restore.title"))
        
        self.str_list = Gtk.StringList()
        self.str_list.append(self.plugin_base.lm.get("actions.counter.long.dropdown.substract"))
        self.str_list.append(self.plugin_base.lm.get("actions.counter.long.dropdown.reset"))

        self.on_long_drop_down = Adw.ComboRow(title=self.plugin_base.lm.get("actions.counter.long.dropdown.title"), model=self.str_list)

        self.save_to_file = Adw.SwitchRow(title=self.plugin_base.lm.get("actions.counter.file.title"))

        self.file_path = Adw.EntryRow(title=self.plugin_base.lm.get("actions.counter.file.path"))

        self.load_defaults()

        self.restore_switch.connect("notify::active", self.on_restore_changed)
        self.on_long_drop_down.connect("notify::selected", self.on_long_drop_down_changed)
        self.save_to_file.connect("notify::active", self.on_save_to_file_changed)
        self.file_path.connect("changed", self.on_file_path_changed)

        return [self.restore_switch, self.on_long_drop_down, self.save_to_file, self.file_path]
    
    def load_defaults(self) -> None:
        settings = self.get_settings()

        self.restore_switch.set_active(settings.get("restore", True))

        self.save_to_file.set_active(settings.get("save_to_file", False))
        self.file_path.set_text(settings.get("file_path", ""))

        if settings.get("on_long_drop_down") == "Substract":
            self.on_long_drop_down.set_selected(0)
        else:
            self.on_long_drop_down.set_selected(1)

    def on_restore_changed(self, switch, *args):
        settings = self.get_settings()
        settings["restore"] = switch.get_active()
        self.set_settings(settings)

    def on_long_drop_down_changed(self, combo, *args):
        settings = self.get_settings()
        if self.on_long_drop_down.get_selected() == 0:
            settings["on_long_drop_down"] = "Substract"
        else:
            settings["on_long_drop_down"] = "Revert"
        self.set_settings(settings)

    def on_save_to_file_changed(self, switch, *args):
        settings = self.get_settings()
        settings["save_to_file"] = switch.get_active()
        self.set_settings(settings)

    def on_file_path_changed(self, entry, *args):
        settings = self.get_settings()
        settings["file_path"] = entry.get_text()
        self.set_settings(settings)

    def on_key_down(self):
        self.key_down_time = time.time()

    def on_key_up(self):
        long_press_treshhold = 0.5

        if time.time() - self.key_down_time >= long_press_treshhold:
            self.on_long_press()
        else:
            self.value += 1
            self.show_value()


    def on_long_press(self):
        settings = self.get_settings()
        if settings.get("on_long_drop_down") == "Substract":
            self.value -= 1
        else:
            self.value = 0
        
        self.show_value()

    def show_value(self) -> None:
        self.set_center_label(str(self.value), font_size=30)

        settings = self.get_settings()
        settings["value"] = self.value
        self.set_settings(settings)

        if settings.get("save_to_file"):
            with open(settings.get("file_path"), "w") as f:
                f.write(str(self.value))

  

class CounterPlugin(PluginBase):
    def __init__(self):
        super().__init__()

        self.init_locale_manager()

        self.lm = self.locale_manager

        ## Register actions
        self.post_request_holder = ActionHolder(
            plugin_base=self,
            action_base=Counter,
            action_id="com_core447_Counter::Counter",
            action_name=self.lm.get("actions.counter.name"),
            icon=Gtk.Picture.new_for_filename(os.path.join(self.PATH, "assets", "POST.png"))
        )
        self.add_action_holder(self.post_request_holder)


        # Register plugin
        self.register(
            plugin_name=self.lm.get("plugin.name"),
            github_repo="https://github.com/StreamController/Counter",
            plugin_version="1.0.0",
            app_version="1.0.0-alpha"
        )

    def init_locale_manager(self):
        self.lm = self.locale_manager
        self.lm.set_to_os_default()

    def get_selector_icon(self) -> Gtk.Widget:
        return Gtk.Image(icon_name="network-transmit-receive")