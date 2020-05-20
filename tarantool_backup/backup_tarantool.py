#!/usr/bin/env python

import sys
# import time
import subprocess
import socket
import tempfile
import os
import glob
from datetime import datetime
import re
import json
import urllib2

RSYNC_LONGTERM_HOST = "longterm.host"
RSYNC_LONGTERM_USER = "tarantool_backup"
RSYNC_LONGTERM_MODULE = "long_term/auto"
RSYNC_PASSWD_FILE = "/usr/palevo/rsync.backup.secret"
SERVER_NAME = socket.getfqdn()
BWLIMIT = 10000

RSYNC = "rsync --bwlimit=%d --recursive --no-relative --timeout=300 --password-file=%s" % (BWLIMIT, RSYNC_PASSWD_FILE)
URL_FOR_STATUS = 'http://go_api.host:5009/create'


def parsing_systemctl_output(dirty_list_instances):
    list_instances = []
    for element in dirty_list_instances:
        try:
            list_instances.append(re.search('(^tarantool\@(.*)\.service).*', element).group(2))
        except Exception as err:
            exit_with_error('Failed parsing tarantool instances from systemctl output', err)
    return list_instances


def get_tarantool_instances():
    "Get tarantool instances from systemctl output"
    command = ['/usr/bin/systemctl', 'list-units', '--state=running', 'tarantool*', '--plain', '--no-legend', '--no-pager']
    try:
        dirty_list_instances = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0].split('\n')[:-1]
    except Exception as err:
        exit_with_error("Failed to get tarantool instances", err)
    return parsing_systemctl_output(dirty_list_instances)


def get_backup_file(instance_name):
    """Get latest file from tarantool dir"""
    try:
        instance_path = os.path.join('/var/tarantool/snaps/', instance_name+"/*")
        list_of_files = glob.glob(instance_path)
    except OSError as err:
        exit_with_error("Couldn't open instance shapshoot dir: %s", err)
    return max(list_of_files, key=os.path.getctime)


def status_file_writer(status_file, message, truncate=False):
    if truncate:
        open(status_file, 'w').close()
    else:
        try:
            with open(status_file, 'a') as f:
                f.writelines(message + '\n')
        except Exception as err:
            exit_with_error("Couldn't writing mon file: %s", err)


def generate_json_status(host="", finished_date="", filename="", status=""):
    status_dict = {
        "host": host,           # host fqdn
        "date": finished_date,  # date finished rsync
        "filename": filename,   # filename snap
        "status": status,       # rsync status
    }
    try:
        return json.dumps(status_dict)
    except json.JSONEncoder as err:
        msg = "Error json encoder: %s" % err
        return json.dumps({"status": msg})


def post_rsync_status_to_mysql(data, url=URL_FOR_STATUS):
    """
    url = url to go_spi server with go api to mysql
    data = json data like format:
        Host            string                  `json:"host"`
        Date            string                  `json:"date"`
        Filename        string                  `json:"filename"`
        Status          string                  `json:"status"`
        Thinning        sql.NullString          `json:"thinning"`
        """
    try:
        req = urllib2.Request(url,
                              headers={
                                  "Content-Type": "application/json",
                                  "Accept": "*/*",
                                  "User-Agent": "backup_status/app", }, data=data)
        f = urllib2.urlopen(req)
    except Exception as err:
        print "Error POST date to %s with err: %s" % (url, err)


class RsyncRunner:
    """
    ::instance_name -  tarantool instance name for backup
    ::status_file - file path for writing status
    ::date_suffix - date when starting backup
    ::backup_snap - snap file name
    """
    def __init__(self, instance_name):
        self.instance_name = instance_name
        self.status_file = os.path.join(tempfile.gettempdir(), 'status.txt')
        self.date_suffix = datetime.now().strftime("%Y-%m-%d-%H-%M")
        self.backup_snap = get_backup_file(instance_name)

    @staticmethod
    def __run_rsync(command, upload_snap=False, snap_file=""):
        try:
            ret = subprocess.call(command, shell=True)
        except subprocess.CalledProcessError as err:
            exit_with_error("Run rsync failed with error: %s", err)
        if ret != 0:
            # if upload snap, then POST status data to mysql
            if upload_snap:
                post_rsync_status_to_mysql(generate_json_status(host=SERVER_NAME,
                                                                finished_date=datetime.now().strftime(
                                                                    "%Y-%m-%d %H-%M-%S"),
                                                                filename=snap_file,
                                                                status="FAILED"
                                                                ))
            else:
                exit_with_error("Rsync exit code not 0: %d", ret)
        else:
            # if upload snap, then POST status data to mysql
            if upload_snap:
                post_rsync_status_to_mysql(generate_json_status(host=SERVER_NAME,
                                                                finished_date=datetime.now().strftime(
                                                                    "%Y-%m-%d %H-%M-%S"),
                                                                filename=snap_file,
                                                                status="DONE"
                                                                ))
            else:
                print {"status": "completed",
                       "completed_command": command,
                       "finished_date": datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                       }

    def __rsync_make_dir(self):
        rsync_dst_path_parts = (RSYNC_LONGTERM_MODULE, SERVER_NAME, self.instance_name)
        dst_path = ""
        for path in rsync_dst_path_parts:
            dst_path += path + "/"
            command = "%s -aq /dev/null --exclude='*' %s@%s::%s" % (
                RSYNC, RSYNC_LONGTERM_USER, RSYNC_LONGTERM_HOST, dst_path
            )
            self.__run_rsync(command)
            # command = "%s -aq /dev/null --exclude='*' %s@%s::%s::%s/" % (RSYNC,  RSYNC_LONGTERM_USER, RSYNC_LONGTERM_HOST, RSYNC_LONGTERM_MODULE)

    def __upload_snap(self):
        command = "%s -aq %s %s@%s::%s/%s/%s/%s/" % (
            RSYNC, self.backup_snap, RSYNC_LONGTERM_USER,
            RSYNC_LONGTERM_HOST, RSYNC_LONGTERM_MODULE,
            SERVER_NAME, self.instance_name, self.date_suffix
        )
        self.__run_rsync(command, upload_snap=True, snap_file=self.backup_snap)
        finished_date = datetime.now().strftime("%Y-%m-%d-%H-%M")
        status_file_writer(self.status_file, "complete: %s" % finished_date)

    def __upload_status_file(self):
        command = "%s -aq %s %s@%s::%s/%s/%s/%s/" % (
            RSYNC, self.status_file, RSYNC_LONGTERM_USER,
            RSYNC_LONGTERM_HOST, RSYNC_LONGTERM_MODULE,
            SERVER_NAME, self.instance_name, self.date_suffix
        )
        self.__run_rsync(command)

    def do_backup(self):
        status_file_writer(self.status_file, "started: %s" % self.date_suffix)
        status_file_writer(self.status_file, SERVER_NAME)

        self.__rsync_make_dir()
        self.__upload_snap()

        self.__upload_status_file()

        # truncate  status file
        status_file_writer(self.status_file, "", truncate=True)


def exit_with_error(text, err):
    print(text, err)
    sys.exit(1)


def main():
    # init runner
    for instance in get_tarantool_instances():
        rsync_runner = RsyncRunner(instance)
        rsync_runner.do_backup()


if __name__ == '__main__':
    main()

