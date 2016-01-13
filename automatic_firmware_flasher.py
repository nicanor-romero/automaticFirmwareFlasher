# coding=utf-8

__author__ = "Nicanor Romero Venier <nicanor.romerovenier@bq.com>"

import serial
import os
import sys
from Tkinter import *
import serial.tools.list_ports
import platform
import threading
import sarge

# **************************************


#HEX_FILE_NAME = "Marlin_hephestos_2-429.hex"
HEX_FILE_NAME = "Marlin_witbox_2-429.hex"



# **************************************

class automaticFirmwareFlasher():

    def __init__(self):
        self.serial_ports_to_ignore = list(serial.tools.list_ports.comports())
        self.start_gui()
        return

    def start_gui(self):
        # Main Window
        self.top = Tk()
        w = self.top.winfo_screenwidth()
        h = self.top.winfo_screenheight()

        self.top.geometry("%dx%d+%d+%d" % (w/2, h/2, w/4, h/4))

        # Init GUI objects
        self.gui_hex_filename = Label(self.top, font=('Verdana', '12'), justify="center", text=HEX_FILE_NAME)
        self.gui_instructions_var = StringVar()
        self.gui_instructions = Label(self.top, font=('Verdana', '18', 'bold'), justify="center", textvariable=self.gui_instructions_var)
        self.gui_flash_result_var = StringVar()
        self.gui_flash_result = Label(self.top, font=('Verdana', '18', 'bold'), justify="center", textvariable=self.gui_flash_result_var)
        
        # Bindings
        self.top.bind("<<go_to_connect_serial_port>>", self._connect_serial_port)
        self.top.bind("<<go_to_serial_port_connected>>", self._serial_port_connected)
        self.top.bind("<<go_to_flash_successful>>", self._flash_successful)
        self.top.bind("<<go_to_flash_failed>>", self._flash_failed)
        self.top.bind("<<go_to_disconnect_serial_port>>", self._disconnect_serial_port)

        # Placements
        self.gui_hex_filename.pack(side=TOP, fill=X, expand=True)
        self.gui_instructions.pack(side=TOP, fill=X, expand=True)
        self.gui_flash_result.pack(side=TOP, fill=X, expand=True)

        # Start procedure
        self.stop_autodetect = False
        self._connect_serial_port()

        # Start GUI
        self.top.mainloop()

        self.stop_autodetect = True
        return

    def _connect_serial_port(self, e=None):
        self.gui_instructions_var.set("Connect Board")
        self.gui_flash_result_var.set("")

        # Start port autodetection thread
        autodetect_serial_port_thread = threading.Thread(target=self._autodetect_serial_port_connected)
        autodetect_serial_port_thread.daemon = False
        autodetect_serial_port_thread.start()

        return

    def _autodetect_serial_port_connected(self):
        while True:
            serial_ports = list(serial.tools.list_ports.comports())
            if len(serial_ports) == len(self.serial_ports_to_ignore) + 1:
                break
            if self.stop_autodetect:
                return

        for s in serial_ports:
            if s not in self.serial_ports_to_ignore:
                if platform.system() == "Windows":
                    s = str(s)
                    self.board_serial_port = s[s.find('('):s.find(')')]
                elif platform.system() == "Linux":
                    self.board_serial_port = s[0]
                break

        self.top.event_generate("<<go_to_serial_port_connected>>", when="tail")
        return

    def _serial_port_connected(self, e=None):
        self.gui_instructions_var.set("Flashing firmware...")

        # Start port autodetection thread
        flash_firmware_thread = threading.Thread(target=self._flash_firmware)
        flash_firmware_thread.daemon = False
        flash_firmware_thread.start()

        return

    def _flash_firmware(self, e=None):

        if platform.system() == "Windows":
            avrdude_filename = "avrdude.exe"
        elif platform.system() == "Linux":
            avrdude_filename = "avrdude"

        avrdude_path = os.path.abspath(os.path.join("utils", avrdude_filename))
        working_dir = os.path.dirname(os.path.abspath(avrdude_path))
        hex_path = os.path.abspath(HEX_FILE_NAME)
        avrdude_command = [avrdude_path, "-p", "m2560", "-c", "wiring", "-P", self.board_serial_port, "-U", "flash:w:" + hex_path + ":i", "-D"]

        '''
        # Simulate flashing
        import time
        print "Simulating command execution: %s" % ' '.join(avrdude_command)
        time.sleep(2)
        self.top.event_generate("<<go_to_flash_failed>>", when="tail")
        return
        '''

        try:
            p = sarge.run(avrdude_command, cwd=working_dir, async=True, stdout=sarge.Capture(), stderr=sarge.Capture())
            p.wait_events()

            while p.returncode is None:
                line = p.stderr.read(timeout=0.5)
                if not line:
                    p.commands[0].poll()
                    continue
                print line

            if p.returncode == 0:
                print "Flashing successful"
                self.top.event_generate("<<go_to_flash_successful>>", when="tail")
            else:
                print "Avrdude returned code {returncode}".format(returncode=p.returncode)
                self.top.event_generate("<<go_to_flash_failed", when="tail")

        except:
            print "Flashing failed."
            self.top.event_generate("<<go_to_flash_failed>>", when="tail")
        
        return

    def _flash_successful(self, e=None):
        self.gui_flash_result.config(fg="green")
        self.gui_flash_result_var.set("Flashing successful")

        self.top.event_generate("<<go_to_disconnect_serial_port>>", when="tail")
        return

    def _flash_failed(self, e=None):
        self.gui_flash_result.config(fg="red")
        self.gui_flash_result_var.set("Flashing failed")

        self.top.event_generate("<<go_to_disconnect_serial_port>>", when="tail")
        return

    def _disconnect_serial_port(self, e=None):
        self.gui_instructions_var.set("Disconnect Board")

        # Start port autodetection thread
        autodetect_serial_port_thread = threading.Thread(target=self._autodetect_serial_port_disconnected)
        autodetect_serial_port_thread.daemon = False
        autodetect_serial_port_thread.start()

        return
        
    def _autodetect_serial_port_disconnected(self):
        while True:
            serial_ports = list(serial.tools.list_ports.comports())
            if len(serial_ports) == len(self.serial_ports_to_ignore):
                break
            if self.stop_autodetect:
                return

        self.top.event_generate("<<go_to_connect_serial_port>>", when="tail")
        return


if __name__ == '__main__':
    main = automaticFirmwareFlasher()