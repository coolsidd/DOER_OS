#!/usr/bin/env python

import gi
import os
import csv
import shutil
import io

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject

import fcntl
import subprocess

PATH_TO_COMPOSE = "~/.doer"


def get_size(start_path="."):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size


def bytes_to_size(num):
    for unit in ["", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]:
        if abs(num) < 1000:
            return "%3.0f%s" % (num, unit)
        num /= 1000
    return "%.0f%s" % (num, "YB")


def size_to_bytes(size):
    units = ["", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]
    size = size.strip()
    size_num = int(size[:-2])
    size_unit = size[-2:]

    return size_num * (10 ** (units.index(size_unit) * 3))


def unblock_fd(stream):
    fd = stream.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)


class StreamTextBuffer(Gtk.TextBuffer):
    """TextBuffer read command output syncronously"""

    def __init__(self, commands, pbar, callback, run_auto=True):
        Gtk.TextBuffer.__init__(self)
        self.failed = False
        self.IO_WATCH_ID = tuple()
        self.commands = commands
        self.run_auto = run_auto
        self.pbar = pbar
        self.callback = callback
        self.index = 0

    def stop(self):
        if len(self.IO_WATCH_ID):
            for id_ in self.IO_WATCH_ID:
                # remove subprocess io_watch if not removed will
                # creates lots of cpu cycles, when process dies
                GLib.source_remove(id_)
            self.IO_WATCH_ID = tuple()
            self.proc.terminate()  # send SIGTERM
        return

    def run(self):
        self.pbar.set_fraction(self.index / len(self.commands))
        if self.failed:
            self.insert_at_cursor("There were errors")
            return
        if self.index >= len(self.commands) and not self.failed:
            self.insert_at_cursor("All applications transferred successfully")
            self.stop()
            self.callback()
            return
        self.insert_at_cursor(self.commands[self.index] + "\n")
        self.proc = subprocess.Popen(
            self.commands[self.index],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        self.index += 1
        self.bind_subprocess(self.proc)

    def bind_subprocess(self, proc):
        unblock_fd(proc.stdout)
        watch_id_stdout = GLib.io_add_watch(
            channel=proc.stdout,
            priority_=GLib.IO_IN | GLib.IO_PRI | GLib.IO_ERR | GLib.IO_HUP,
            condition=self.buffer_update,
            # func      = lambda *a: print("func") # when the condition is satisfied
            # user_data = # user data to pass to func
        )
        unblock_fd(proc.stderr)
        watch_id_stderr = GLib.io_add_watch(
            channel=proc.stderr,
            priority_=GLib.IO_IN | GLib.IO_PRI | GLib.IO_ERR | GLib.IO_HUP,
            condition=self.buffer_update,
            # func      = lambda *a: print("func") # when the condition is satisfied
            # user_data = # user data to pass to func
        )
        watch_id_timeout = GLib.timeout_add_seconds(1, self.buffer_update)

        self.IO_WATCH_ID = (watch_id_stdout, watch_id_stderr, watch_id_timeout)
        return self.IO_WATCH_ID

    def buffer_update(self, stream=None, condition=None):
        # self.proc.wait()
        if (
            condition == (GLib.IO_IN | GLib.IO_PRI | GLib.IO_ERR | GLib.IO_HUP)
            or condition is None
        ):
            strout = self.proc.stdout.read()
            strerr = self.proc.stderr.read()
            print(strout)
            print(strerr)
            if strout is not None or strerr is not None:
                self.insert_at_cursor(strout)
                self.insert_at_cursor(strerr)

        result = self.proc.poll()
        if result is not None:
            self.stop()
            if result != 0:
                self.insert_at_cursor("Failed with exit code {}".format(result))
                self.failed = True
                return False
            if self.run_auto:
                self.run()
            return False
        else:
            return True


class MyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Replicate DOER_OS")

        self.screens = [
            Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6) for x in range(3)
        ]
        self.add(self.screens[0])
        self.current_screen = 0
        self.welcome_label = Gtk.Label(
            label="Welcome to the Replication Script for DOER_OS"
        )
        self.screen1_hbox2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.screen1_hbox2.pack_end(self.welcome_label, True, True, 50)
        self.screens[0].pack_start(self.screen1_hbox2, True, True, 50)
        self.button1 = Gtk.Button(label="Next")
        self.screen1_hbox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.screen1_hbox1.pack_end(self.button1, False, False, 25)
        self.screens[0].pack_start(self.screen1_hbox1, False, True, 25)
        self.button1.connect("clicked", self.get_installed_list)
        self.button1.connect("clicked", self.next_screen)

        self.installed_list = []
        self.commands = []
        self.checkboxes_scrollable = Gtk.ScrolledWindow()
        self.checkbox_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        Gtk.Container.add(self.checkboxes_scrollable, self.checkbox_vbox)
        self.screens[1].pack_start(self.checkboxes_scrollable, True, True, 6)
        self.button2 = Gtk.Button(label="Destination")
        self.button2.connect("clicked", self.get_final_storage_location)
        self.button3 = Gtk.Button(label="Store")
        self.button3.connect("clicked", self.store)
        self.button3.connect("clicked", self.next_screen)
        self.button3.set_sensitive(False)
        self.size_bar = Gtk.ProgressBar()
        self.screens[1].pack_end(self.button2, False, True, 6)
        self.screens[1].pack_end(self.button3, False, True, 6)
        self.screens[1].pack_end(self.size_bar, False, True, 6)
        self.path_to_dest = None
        self.utilized = self.free = 0
        # The following will be replaced in the commands before executing
        # 0 -> size
        # 1 -> name
        # 2 -> tag NOTE IN case of folders, it returns "None"
        # 3 -> id (of docker image), NOTE IN case of folders, it returns "None"
        # 4 -> path_to_compose_dir
        # 5 -> path_to_storage (final directory)
        #
        # 0 -> size
        # 1 -> name
        # 2 -> path_to_store (~/.doer)
        # 3 -> path_to_dest (final directory where the tar files are located)
        self.supported_list = {
            "kolibri_doer": [
                "echo Making Directory",
                'mkdir -p "{5}"',
                "echo Storing tar",
                'docker save "{1}:{2}" -o "{5}/{1}.tar"',
                "echo copying setupfiles",
                'rsync -a --exclude=\'*.tar\'  "{4}/{1}/"* "{5}"',
                "echo Done",
            ],
            "sugarizer-server_mongodb": [
                "echo Making Directory",
                'mkdir -p "{5}"',
                "echo Storing tar",
                'docker save "{1}:{2}" -o "{5}/{1}.tar"',
                "echo copying setupfiles",
                'rsync -a --exclude=\'*.tar\'  "{4}/{1}/"* "{5}"',
                "echo Done",
            ],
            "sugarizer-server_server": [
                "echo Making Directory",
                'mkdir -p "{5}"',
                "echo Storing tar",
                'docker save "{1}:{2}" -o "{5}/{1}.tar"',
                "echo copying setupfiles",
                'rsync -a --exclude=\'*.tar\'  "{4}/{1}/"* "{5}"',
                "echo Done",
            ],
            "turtleblocks": [
                "echo Making Directory",
                'mkdir -p "{5}"',
                "echo copying setupfiles",
                'rsync -a --exclude=\'*.tar\'  "{4}/{1}/"* "{5}"',
                "echo Done",
            ],
            "musicblocks": [
                "echo Making Directory",
                'mkdir -p "{5}"',
                "echo copying setupfiles",
                'rsync -a --exclude=\'*.tar\'  "{4}/{1}/"* "{5}"',
                "echo Done",
            ],
            "edgy": [
                "echo Making Directory",
                'mkdir -p "{5}"',
                "echo copying setupfiles",
                'rsync -a --exclude=\'*.tar\'  "{4}/{1}/"* "{5}"',
                "echo Done",
            ],
            "snap": [
                "echo Making Directory",
                'mkdir -p "{5}"',
                "echo copying setupfiles",
                'rsync -a --exclude=\'*.tar\'  "{4}/{1}/"* "{5}"',
                "echo Done",
            ],
        }
        #
        # Names in the following folder will be checked for in PATH_TO_COMPOSE ( ~/.doer)
        self.supported_folders = ["turtleblocks", "musicblocks", "edgy", "snap"]

        self.button_finished = Gtk.Button(label="Done")
        self.button_finished.set_sensitive(False)
        self.button_finished.connect("clicked", self.next_screen)
        self.final_pbar = Gtk.ProgressBar()
        self.screens[2].pack_end(self.final_pbar, False, True, 6)
        self.screens[2].pack_end(self.button_finished, False, True, 6)

    def generate_commands(self):
        return self.commands

    def store(self, widget):
        for size, chbox, name, tag, _id in self.installed_list:
            if chbox.get_active():
                self.commands.extend(
                    x.format(
                        size,
                        name,
                        tag,
                        _id,
                        PATH_TO_COMPOSE,
                        os.path.join(self.path_to_dest, name),
                    )
                    for x in self.supported_list[name]
                )
        self.scroll = Gtk.ScrolledWindow()
        self.buff = StreamTextBuffer(self.commands, self.final_pbar, self.finish)
        self.buff.run()
        self.textview = Gtk.TextView.new_with_buffer(self.buff)
        self.scroll.add(self.textview)
        self.screens[2].pack_end(self.scroll, True, True, 6)

    def finish(self):
        self.button_finished.set_sensitive(True)

    def calculate_space(self, widget):
        if self.path_to_dest is not None:
            self.free = shutil.disk_usage(self.path_to_dest).free
        self.utilized = 0
        for size, chbox, name, tag, _id in self.installed_list:
            if chbox.get_active():
                self.utilized += size_to_bytes(size)

        if self.free != 0:
            self.size_bar.set_fraction(self.utilized / self.free)
            self.size_bar.set_text("{} / {}".format(self.utilized, self.free))
            self.size_bar.props.show_text = True
        if self.utilized < self.free:
            self.button3.set_sensitive(True)
        else:
            self.button3.set_sensitive(False)

    def get_final_storage_location(self, widget):
        self.file_chooser = Gtk.FileChooserDialog(
            title="Choose output location",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE,
                Gtk.ResponseType.ACCEPT,
            ),
        )
        response = self.file_chooser.run()
        temp_filename = self.file_chooser.get_filename()
        self.file_chooser.destroy()
        if response == Gtk.ResponseType.ACCEPT and temp_filename is not None:
            self.path_to_dest = temp_filename
            self.calculate_space(None)

    def get_installed_list(self, widget):
        dockers = os.popen(
            'docker images -a --format "{{.ID}}|{{.Repository}}|{{.Tag}}|{{.Size}}"'
        ).read()
        csv_reader = csv.reader(io.StringIO(dockers), delimiter="|")
        self.found_images = {
            name: (_id, name, size, tag)
            for _id, name, tag, size in csv_reader
            if name in self.supported_list.keys()
            and os.path.exists(os.path.join(PATH_TO_COMPOSE, name))
        }
        for directory in os.scandir(PATH_TO_COMPOSE):
            name = os.path.basename(directory.path)
            print(name)
            if name in self.supported_folders:
                self.found_images[name] = [
                    "None",
                    name,
                    bytes_to_size(get_size(os.path.join(PATH_TO_COMPOSE, name))),
                    "None",
                ]
        for name, items in self.found_images.items():
            _id = items[0]
            size = items[2]
            tag = items[3]
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            chbox = Gtk.CheckButton(label=name)
            size_label = Gtk.Label(size)
            self.installed_list.append((size, chbox, name, tag, _id))
            chbox.connect("toggled", self.calculate_space)
            hbox.pack_start(chbox, True, True, 6)
            hbox.pack_end(size_label, False, False, 6)
            self.checkbox_vbox.pack_end(hbox, True, True, 6)
            Gtk.Widget.show_all(self.screens[1])

    def next_screen(self, widget):
        Gtk.Widget.destroy(self.screens[self.current_screen])
        self.current_screen += 1
        if self.current_screen >= len(self.screens):
            Gtk.main_quit()
            return

        self.add(self.screens[self.current_screen])
        self.screens[self.current_screen].show_all()


def main():
    win = MyWindow()
    global PATH_TO_COMPOSE
    print(PATH_TO_COMPOSE)
    PATH_TO_COMPOSE = os.path.abspath(os.path.expanduser(PATH_TO_COMPOSE))
    print(PATH_TO_COMPOSE)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
