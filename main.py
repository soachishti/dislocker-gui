import psutil
from subprocess import call, Popen, PIPE
import os
import sys
import logging
from time import sleep

from tkinter import *
        
logging.basicConfig(level=logging.DEBUG)

MSG_PERMISSION_DENIED   = "Permission denied"
MSG_VOLUME_HEADER       = "Cannot parse volume header"
MSG_INVALID_DECRYPT         = "None of the provided decryption mean is decrypting the keys"

class DislockerGUI():
    bitlocker_path = "/media/bitlocker"
    
    def __init__(self):
        # sudo permission check
        if os.getuid() != 0:
            raise Exception("Permission required, run with sudo.")

    def is_bitlocker_disk(self, disk):
        cmd = "dislocker -r -V {}".format(disk)

        p = Popen(cmd.split(" "), stdout=PIPE)
        stdout = p.stdout.read()

        print disk
        print stdout
        print "="*80

        if MSG_VOLUME_HEADER in stdout:
            return False
        elif MSG_INVALID_DECRYPT in stdout:
            return True
        else:
            raise Exception(stdout)

    def __get_disks(self):
        # https://github.com/MrVallentin/mount.py/blob/master/mount.py
        # Return USB or External Drive's Partitions
        with open("/proc/partitions", "r") as f:
            devices = []
            
            for line in f.readlines()[2:]: # skip header lines
                words = [ word.strip() for word in line.split() ]
                minor_number = int(words[1])
                device_name = words[3]
                
                if (minor_number % 16) == 0:
                    path = "/sys/class/block/" + device_name
                    
                    if os.path.islink(path):
                        if os.path.realpath(path).find("/usb") > 0:
                            device = "/dev/" + device_name
                            cmd = "fdisk -l {}".format(device)
                            p = Popen(cmd, stdout=PIPE, shell=True)
                            stdout = p.stdout.read()
                            partitions = stdout.split("\n")[-2].split()[0].strip()
                            
                            devices.append(partitions)
            
            return devices

    def __get_mount_path(self, device):
        name = os.path.basename(device)
        path = "/media/" + name
        return path

    def __is_mounted(self, device):
        return os.path.ismount(self.__get_mount_path(device))

    def __get_size(self, device):
        path = "/sys/block/" + os.path.basename(device)[:3] + "/size"
        print path
        if os.path.exists(path):
            with open(path, "r") as f:
                size = int(f.read().strip()) * 512
                size = str(size / 1024 ** 3)
                return "({} GB)".format(size)

        return "()"

    def get_unmounted_disks(self):
        disks = []
        media_device = self.__get_disks()
        logging.debug("Media Device Found: " + str(media_device))
        for device in media_device:
            if self.__is_mounted(device) == False:
                disks.append(device)
        logging.debug("Unmounted Device: " + str(disks))
        return disks

    def mount(self, device, password):
        mount_path = self.__get_mount_path(device)
        
        os.system("mkdir -p " + mount_path)
        os.system("mkdir -p " + self.bitlocker_path)

        cmd = "dislocker -r -V {} -u{} -- {} ; ".format(device, password, self.bitlocker_path)
        cmd += "mount -r -o loop {}/dislocker-file {}".format(self.bitlocker_path, mount_path)

        logging.debug("Mounting device to " + mount_path)
        logging.debug("Executing command: " + cmd)

        p = Popen(cmd, stdout=PIPE, shell=True)

        #while self.__is_mounted(mount_path):
        #    logging.debug("Waiting for " + mount_path + " to mount")
        #    sleep(1)
            
    def unmount(self, device):
        cmd = "unmount {}".format(self.__get_mount_path(device))
        p = Popen(cmd.split(" "))
        
    def passwordDialog(self, device):
        self.password = ''

        root = Tk()
        root.title("Dislocker GUI")
        pwdbox = Entry(root, show = '*')
        def onpwdentry(evt):
            self.password = pwdbox.get()
            root.destroy()
        def onokclick():
            self.password = pwdbox.get()
            root.destroy()
        
        device_info = 'Device: ' + device + self.__get_size(device)

        Label(root, text = device_info).pack(side = 'top')

        Label(root, text = 'Enter Password').pack(side = 'top')

        pwdbox.pack(side = 'top')
        pwdbox.bind('<Return>', onpwdentry)
        Button(root, command=onokclick, text = 'Submit').pack(side = 'top')

        root.mainloop()
        return self.password

    def run(self):
        while True:    
            devices = d.get_unmounted_disks()
            if len(devices) != 0:
                device = devices[0]
                password = self.passwordDialog(device)
                d.mount(device, password)
                sleep(3000)

d = DislockerGUI()
d.run()
