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

PATH_TO_STORE = "~/.doer/"


def get_size(start_path="."):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size


def size_to_bytes(size):
    units = ["", "KB", "MB", "GB", "TB"]
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
            shell=True,
        )
        self.index += 1
        self.bind_subprocess(self.proc)

    def bind_subprocess(self, proc):
        # unblock_fd(proc.stdout)
        # watch_id_stdout = GLib.io_add_watch(
        #     channel=GLib.IOChannel(proc.stdout.fileno()),
        #     priority_=GLib.IO_IN,
        #     condition=self.buffer_update,
        # )
        # unblock_fd(proc.stderr)
        # watch_id_stderr = GLib.io_add_watch(
        #     channel=GLib.IOChannel(p.stderr.fileno()),
        #     priority_=GLib.IO_IN,
        #     condition=self.buffer_update,
        # )
        watch_id_timeout = GLib.timeout_add(200, self.buffer_update)

        self.IO_WATCH_ID = [watch_id_timeout]
        # self.IO_WATCH_ID = (watch_id_stdout, watch_id_stderr)
        return self.IO_WATCH_ID

    def buffer_update(self):
        # self.proc.wait()
        # stdout = self.proc.stdout.read()
        # stderr = self.proc.stderr.read()
        #

        # if stdout is not None:
        #     self.insert_at_cursor(
        #         stdout if type(stdout) is str else stdout.decode("utf-8")
        #     )
        # if stderr is not None:
        #     self.insert_at_cursor(
        #         stderr if type(stderr) is str else stderr.decode("utf-8")
        #     )
        result = self.proc.poll()
        for out in iter(lambda: self.proc.stdout.read(1), b""):  #
            self.insert_at_cursor(out.decode("utf-8"))
        for out in iter(lambda: self.proc.stderr.read(1), b""):  #
            self.insert_at_cursor(out.decode("utf-8"))
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
        Gtk.Window.__init__(self, title="Install DOER packages")

        self.screens = [
            Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6) for x in range(3)
        ]
        self.add(self.screens[0])
        self.current_screen = 0
        self.welcome_label = Gtk.Label(
            label="Welcome to the Installation Script for DOER_OS"
        )
        self.screens[0].pack_start(self.welcome_label, True, True, 0)

        self.button1 = Gtk.Button(label="Next")
        self.screens[0].pack_start(self.button1, False, True, 0)
        self.button1.connect("clicked", self.get_installed_list)
        self.button1.connect("clicked", self.next_screen)
        self.installed_list = []
        self.commands = []
        self.checkboxes_scrollable = Gtk.ScrolledWindow()
        self.checkbox_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        Gtk.Container.add(self.checkboxes_scrollable, self.checkbox_vbox)
        self.screens[1].pack_start(self.checkboxes_scrollable, True, True, 6)
        self.button2 = Gtk.Button(label="Folder")
        self.button2.connect("clicked", self.get_storage_location)
        self.button3 = Gtk.Button(label="Load")
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
        # 2 -> path_to_store (~/.doer)
        # 3 -> path_to_dest (final directory where the tar files are located)
        self.default_list = {
            "turtleblocks": [
                "echo Making Directory",
                'mkdir -p "{2}/{1}"',
                "echo Cloning git",
                'echo "This may take a while..."',
                'rm -Rf "{2}/temp/"',
                'git clone "https://github.com/sugarlabs/turtleblocksjs.git" "{2}/temp/turtleblock_git" -v',
                'rsync -av "{2}/temp/turtleblock_git" "{2}/{1}"',
                'rm -Rf "{2}/temp"',
                "echo Done",
            ],
            "physics_video_player": [
                "echo Making Directory",
                'mkdir -p "{2}/{1}"',
                "echo Cloning git",
                'echo "This may take a while..."',
                'rm -Rf "{2}/temp/"',
                'git clone "https://github.com/CLIxIndia-Dev/physics-video-player.git" "{2}/temp/physics_video_player_git" -v',
                'rsync -av "{2}/temp/physics_video_player_git" "{2}/{1}"',
                'rm -Rf "{2}/temp"',
                "echo Done",
            ],
        }
        self.supported_list = {
            "kolibri_doer": [
                "echo Making Directory",
                'mkdir -p "{2}/{1}"',
                "echo Loading tar",
                'docker load < "{3}/{1}.tar"',
                "echo copying setupfiles",
                'rsync -a --exclude=\'*.tar\' "{3}" "{2}"',
                "echo Starting container",
                'cd "{2}/{1}/"',
                'bash "{2}/{1}/install.sh"',
                "echo Done",
            ],
            "sugarizer-server_mongodb": [
                "echo Making Directory",
                'mkdir -p "{2}/{1}"',
                "echo Loading tar",
                'docker load < "{3}/{1}.tar"',
                "echo copying setupfiles",
                'rsync -a --exclude=\'*.tar\' "{3}" "{2}"',
                "echo Starting container",
                'cd "{2}/{1}/"',
                'bash "{2}/{1}/install.sh"',
                "echo Done",
            ],
            "sugarizer-server_server": [
                "echo Making Directory",
                'mkdir -p "{2}/{1}"',
                "echo Loading tar",
                'docker load < "{3}/{1}.tar"',
                "echo copying setupfiles",
                'rsync -a --exclude=\'*.tar\' "{3}" "{2}"',
                "echo Starting container",
                'cd "{2}/{1}/"',
                'bash "{2}/{1}/install.sh"',
                "echo Done",
            ],
            "turtleblocks": [
                "echo Making Directory",
                'mkdir -p "{2}/{1}"',
                "echo Moving Folder",
                'echo "This may take a while..."',
                'rsync -a "{3}" "{2}"',
                "echo Starting Website",
                'cd "{2}/{1}/"',
                'bash "{2}/{1}/install.sh"',
                "echo Done",
            ],
            "musicblocks": [
                "echo Making Directory",
                'mkdir -p "{2}/{1}"',
                "echo Moving Folder",
                'echo "This may take a while..."',
                'rsync -a "{3}" "{2}"',
                "echo Starting Website",
                'cd "{2}/{1}/"',
                'bash "{2}/{1}/install.sh"',
                "echo Done",
            ],
            "edgy": [
                "echo Making Directory",
                'mkdir -p "{2}/{1}"',
                "echo Moving Folder",
                'echo "This may take a while..."',
                'rsync -a "{3}" "{2}"',
                "echo Starting Website",
                'cd "{2}/{1}/"',
                'bash "{2}/{1}/install.sh"',
                "echo Done",
            ],
            "snap": [
                "echo Making Directory",
                'mkdir -p "{2}/{1}"',
                "echo Moving Folder",
                'echo "This may take a while..."',
                'rsync -a "{3}" "{2}"',
                "echo Starting Website",
                'cd "{2}/{1}/"',
                'bash "{2}/{1}/install.sh"',
                "echo Done",
            ],
        }

        self.button_finished = Gtk.Button(label="Done")
        self.button_finished.set_sensitive(False)
        self.button_finished.connect("clicked", self.next_screen)
        self.final_pbar = Gtk.ProgressBar()
        self.screens[2].pack_end(self.final_pbar, False, True, 6)
        self.screens[2].pack_end(self.button_finished, False, True, 6)

    def generate_commands(self):
        return self.commands

    def store(self, widget):
        for chbox, name, path, size in self.installed_list:
            if chbox.get_active():
                if path != "online":
                    self.commands.extend(
                        x.format(
                            size,
                            name,
                            PATH_TO_STORE,
                            os.path.join(self.path_to_dest, name),
                        )
                        for x in self.supported_list[name]
                    )
                elif name in self.default_list:
                    self.commands.extend(
                        x.format(size, name, PATH_TO_STORE, path)
                        for x in self.default_list[name]
                    )
                else:
                    raise KeyError("Unknown name crept into install list")

        self.scroll = Gtk.ScrolledWindow()
        self.buff = StreamTextBuffer(self.commands, self.final_pbar, self.finish)
        self.buff.run()
        self.textview = Gtk.TextView.new_with_buffer(self.buff)
        # TODO ADD Autoscroll
        # self.buff.connect(
        #     "changed",
        #     lambda obj: self.textview.scroll_mark_onscreen(
        #         self.textview, self.buff.get_mark()
        #     ),
        # )

        self.scroll.add(self.textview)
        self.screens[2].pack_end(self.scroll, True, True, 6)

    def finish(self):
        self.button_finished.set_sensitive(True)

    def calculate(self, widget):
        self.free = shutil.disk_usage(PATH_TO_STORE).free
        self.utilized = 0
        for chbox, name, path, size in self.installed_list:
            if chbox.get_active():
                self.utilized += size
        if self.free != 0:
            self.size_bar.set_fraction(self.utilized / self.free)
            self.size_bar.set_text("{} / {}".format(self.utilized, self.free))
            self.size_bar.props.show_text = True
        if self.utilized < self.free and self.utilized != 0 and self.free != 0:
            self.button3.set_sensitive(True)
        else:
            self.button3.set_sensitive(False)

    def get_storage_location(self, widget):
        self.file_chooser = Gtk.FileChooserDialog(
            title="Choose output location",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
            buttons=(
                "_Cancel",
                Gtk.ResponseType.CANCEL,
                "_OK",
                Gtk.ResponseType.ACCEPT,
            ),
        )
        response = self.file_chooser.run()
        self.path_to_dest = self.file_chooser.get_filename()
        self.file_chooser.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            self.get_installed_list(None)

    def get_installed_list(self, widget):
        self.found_images = {}
        if self.path_to_dest is not None:
            # for root, dirs, files in os.walk(self.path_to_dest):
            #     print(dirs)
            for directory_obj in os.scandir(self.path_to_dest):
                directory = os.path.basename(directory_obj.path)
                if directory in self.supported_list.keys():
                    self.found_images[directory] = [
                        os.path.join(self.path_to_dest, directory),
                        get_size(os.path.join(self.path_to_dest, directory)),
                    ]

        # print(self.found_images)
        for name in self.default_list.keys():
            self.found_images.setdefault(
                name, ["online", 1000]
            )  # TODO Add correct git repo sizes
            #
        # print(self.found_images)
        for widget in self.checkbox_vbox:
            self.checkbox_vbox.remove(widget)

        for name, items in self.found_images.items():
            path = items[0]
            size = items[1]
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

            chbox = Gtk.CheckButton(label=name)
            chbox.connect("toggled", self.calculate)
            self.installed_list.append((chbox, name, path, size))
            hbox.pack_start(chbox, True, True, 6)

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
    global PATH_TO_STORE
    # print(PATH_TO_STORE)
    PATH_TO_STORE = os.path.abspath(os.path.expanduser(PATH_TO_STORE))
    # print(PATH_TO_STORE)
    os.popen("mkdir -p {}".format(PATH_TO_STORE))
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
