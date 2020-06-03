#!/usr/bin/python

import subprocess
import re
import socket
import sys
import argparse


HOSTNAME = socket.gethostname().split('.')[0]

# smartctl atribute name for regexp find
PATTERN = {
    #"ctemp": "Temperature_Celsius",
    "relocated": "Reallocated_Event_Count",
    "pending": "Current_Pending_Sector",
}


def call_fdisk(disk):
    fdisk_out = subprocess.Popen("fdisk -l /dev/" + disk, shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE).communicate()[0]
    space = re.findall('Disk /dev/s\w+: (.*) GB,.* bytes', fdisk_out, re.MULTILINE)
    #space is array, zero elemet is capacity
    return space[0]


def is_system_disk(space):
    try:
        if int(float(space)) < 1000:
            print "Is system disk with space %s" % space
            return True
    except ValueError as e:
        print "error formating disk %s" % e


def exit_with_error(text, err):
    print(text, err)
    sys.exit(1)


class SmartStat:
    def __init__(self, smart_attr_name):
        self.smart_attr_name = smart_attr_name

    def get_attr_value(self):
        # get disks from /sys/block
        try:
            sys_block_output = subprocess.Popen("ls -al /sys/block/sd*/device", shell=True, stdin=subprocess.PIPE,
                                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            print e
            sys.exit(1)
        except Exception as e:
            sys.stderr.write("can't get disks from sys/block \n")
            print e
            sys.exit(1)

        dirty_disks_name = sys_block_output.communicate()[0]

        # reduction disk name to sd[a-z]+
        DISKS = re.findall("block/(.*)/device -> ../../(?:devices/pci|../)", dirty_disks_name, re.MULTILINE)
        HDDs = {}

        # iterating and exec smartctl by each disk
        for d in DISKS:
            if is_system_disk(call_fdisk(d)):
                try:
                    smart_out = subprocess.Popen("/usr/sbin/smartctl -xad sat /dev/" + d, shell=True, stdin=subprocess.PIPE,
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except OSError as e:
                    print e
                    sys.exit(1)
                except Exception as e:
                    sys.stderr.write("can't get smart from disk %s\n" % d)
                    sys.exit(1)

                smart_out_q = smart_out.communicate()[0]
                # base hash with disks
                HDDs[d] = {}

                # get key and value from const PATTERN, keys usage for internal, value usage for smartctl output parsing
                for param_key, param_smart_name in self.smart_attr_name.items():
                    pattern = param_smart_name + ".*\-\s+(\d+)"
                    smart_found_value = re.findall(pattern, smart_out_q, re.MULTILINE)

                # add smartctl status hash to base hash, will be see like {"sdaaa": {"smart_stat": 100500}}
                    if smart_found_value:
                        HDDs[d][param_key] = int(smart_found_value[-1])
        return HDDs


class Monitoring:
    def __init__(self, hash_stats, out_monitoring_file):
        self.hash_stats = hash_stats
        self.out_monitoring_file = out_monitoring_file

    def write_to_file(self, messages=[], truncate_file=False):
        """writing messages to mon_file"""
        if truncate_file:
            try:
                open(self.out_monitoring_file, 'w').close()
            except IOError as err:
                exit_with_error("I/O error", err)
        else:
            try:
                with open(self.out_monitoring_file, 'a') as f:
                    for msg in messages:
                        f.writelines(msg)
            except IOError as err:
                exit_with_error("I/O error", err)

    def parsing_stat(self):
        """parsing dictinary with smartctl stats """
        monitoring_messages = []
        for disk, stats in self.hash_stats.items():
            if stats['relocated'] > 0 or stats['pending'] > 0:
                monitoring_messages.append(
                    "Attention! Disk %s Pending_Sector = %s Reallocated = %s\n" % (disk,  stats['pending'], stats['relocated']))
        # if all stats is OK, then truncate monfile
        if len(monitoring_messages) == 0:
            self.write_to_file(truncate_file=True)

        # writing date to file, if disk is bad
        self.write_to_file(messages=monitoring_messages)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', required=True, help='usage -f /tmp/monfile.txt for writing to file')
    args = parser.parse_args()

    smartStat = SmartStat(PATTERN)
    smart_data = smartStat.get_attr_value()
   # print smart_data
    mon = Monitoring(smart_data, args.file)
    mon.parsing_stat()


if __name__ == '__main__':
    main()

