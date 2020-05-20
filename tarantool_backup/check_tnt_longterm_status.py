#!/usr/bin/env python
import requests
from requests.exceptions import HTTPError
import sys
import json
import argparse


CHECK_URL = "http://127.0.0.1:5009/status"


def get_request(url):
    try:
        response = requests.get(url)

        response.raise_for_status()
    except HTTPError as http_err:
        print "HTTP error occurred: %s" % http_err
        sys.exit(1)
    except Exception as err:
        print "HTTP error occurred: %s" % err
        sys.exit(1)
    return response.content


def parsing_status_output(response_body):
    mon_array = []
    try:
        response_body_array = json.loads(response_body)
        if len(response_body_array) == 0:
            return []
        else:
            for item in response_body_array:
                mon_array.append("HOST: %s, DATE: %s, STATUS: %s <br>" % (item['host'], item['date'], item['status']))
    except json.JSONDecodeError as err:

        print "Error decode json from response: %s" % err
        sys.exit(1)
    return mon_array


def write_mon_file(list_monitoring, mon_file):
    if len(list_monitoring) > 0:
        try:
            with open(mon_file, 'a') as f:
                f.writelines("DONT CALL AT NIGHT!!!!!!!" + '\n')
                for line in list_monitoring:
                    f.writelines(line + '\n')
        except Exception as err:
            print "Couldn't writing mon file: %s", err
            sys.exit(1)
    else:
        open(mon_file, 'w').close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--out', type=str, help='usage (-o|--out) output monfile', required=True)
    args = parser.parse_args()

    # truncate mon file, need for avoiding overwrite
    try:
        open(args.out, 'w').close()
    except Exception:
        print "Error truncate mon file"

    write_mon_file(parsing_status_output(get_request(CHECK_URL)), args.out)


if __name__ == '__main__':
    main()

