import sys
import configparser
import argparse
import os
import re
import glob
import urllib2

import json

DEFAULT_KEY_PATH = "./backup_clean.ini"


def _get_private(filename=None):
    data = {"url": ""}
    if filename:
        try:
            reader = configparser.RawConfigParser()
            reader.read(filename)
            data['url'] = reader.get('api', 'url')
        except configparser.NoSectionError as e:
            print "Error config parse:  %s" % e
            sys.exit(1)
    else:
        return "Not found"
    return data


def parsing_date(date):
    """Convert data to backup format"""
    return '-'.join(date.split())


def parsing_file_path(snap_file):
    """
    :param snap_file: - path to snap from api
    :return: nested list. Get 0 slice in which 0 element is instance name. 1 element - snap's filename
    """
    return re.findall(r"^\/var\/tarantool\/snaps\/([a-z_]+\d)\/(.*\.snap)", snap_file)


def get_path_to_backup_for_clean(hostname, date, instance_name, snap_file):
    static_part_of_path = "/data/backup/long_term/"
    snap_path = os.path.join(static_part_of_path, hostname + "/" + instance_name + "/" + date[:-8] +"*/"+snap_file)
    return glob.glob(snap_path)


def get_json_from_api(url, timeout=2):
    """
    :param url: url to server with backup api
    :param timeout: timeout to host. Default 2 sec
    :return: array with dict [{
                                "backup_id": 396,
                                "host": "my_tarantool_host",
                                "date": "2020-03-30 00-00-00",
                                "filename": "/var/tarantool/snaps/instance_name1/00000000000000000000.snap",
                                "status": "",
                                "thinning": {
                                  "String": "",
                                  "Valid": false
                                }]
    """
    try:
        api_response = urllib2.urlopen(url + '/thinning', timeout=timeout)
    except Exception as err:
        print "Can't get data from api with error: %s" % err
    try:
        return json.loads(api_response.read())
    except ValueError:  # includes simplejson.decoder.JSONDecodeError
        print 'Decoding JSON has failed'
        sys.exit(1)


def post_update_thinning_status(backup_id, url="http://127.0.0.1:5001"):
    """
    url = url to go_API server with go api to mysql
    backup_id = backup_id for which update thinning status
        """
    try:
        req = urllib2.Request(url + "/update/" + str(backup_id),
                              headers={
                                  "Accept": "*/*",
                                  "User-Agent": "backup_cleaner/app",
                                  },
                              data="")
        f = urllib2.urlopen(req)
        print f.read()

    except Exception as err:
        print "Error POST date to %s with err: %s" % (url, err)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, help='path to mysql auth data, if not set,try usage ~/.my.cnf')
    args = parser.parse_args()

    if args.config:
        conf_dict = _get_private(args.config)
    else:
        conf_dict = _get_private(DEFAULT_KEY_PATH)

    json_data = get_json_from_api(conf_dict['url'])
    for row_dict in json_data:
        try:
            #os.remove(get_path_to_backup_for_clean(temp_dict['host'],  temp_dict['date'], temp_dict['instance_name'], temp_dict['filename'])[0])
            os.remove(get_path_to_backup_for_clean(row_dict['host'],
                                               parsing_date(row_dict['date']),
                                               parsing_file_path(row_dict['filename'])[0][0],
                                               parsing_file_path(row_dict['filename'])[0][1]
                                               )[0]
                  )
            post_update_thinning_status(row_dict['backup_id'], url=conf_dict['url'])
        except Exception as err:
            print "Error delete snap or POST status: %s" % err


if __name__ == '__main__':
    main()


