#!/usr/bin env python
import subprocess
import re
import sys
import argparse


class GetPsOutput:
    def __init__(self, process_name_for_grep, regexp_text_for_get_rss_usaged):
        self.process_name_for_grep = process_name_for_grep
        self.regexp_text_for_get_rss_usaged = regexp_text_for_get_rss_usaged

    def get_process_rss(self):
        try:
            ps_output = subprocess.Popen(['ps', '-eo', 'rss,cmd'], stdout=subprocess.PIPE)
            grep_out = subprocess.Popen(['grep', self.process_name_for_grep], stdin=ps_output.stdout,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ps_output.stdout.close()
            out = grep_out.communicate()[0]
            return conv_KB_to_MB(int(re.findall(r"(\d+ %s)" % self.regexp_text_for_get_rss_usaged, out)[0].split()[0]))
        except Exception as err:
            print "Failed to get and parsing ps output %s" % err
            sys.exit(1)


def conv_KB_to_MB(input_kilobyte):
    megabyte = float(0.000976562)
    convert_mb = input_kilobyte * megabyte
    return convert_mb


def write_mon_file(list_monitoring, mon_file):
    if len(list_monitoring) > 0:
        try:
            with open(mon_file, 'a') as f:
                for line in list_monitoring:
                    f.writelines(line + '\n')
        except Exception as err:
            print "Couldn't writing mon file: %s" % err
            sys.exit(1)
    else:
        open(mon_file, 'w').close()


def convert_string_to_int(string):
    try:
        return int(string)
    except ValueError as err:
        print "Error converting %s to integer with error: %s" % (string, err)
        sys.exit(1)


def check_instance_limit(current_instance_rss, alarm_rss, message_list=[], inst_name="Pairdb"):
    if current_instance_rss > alarm_rss:
        message_list.append("%s instance usage %d MB RSS" % (inst_name, current_instance_rss))
        return message_list
    else:
        return message_list


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--out', type=str, help='usage (-o|--out) output mon_file', required=True)
    parser.add_argument('-l', '--limit', type=str, help='usage (-l|--limit) limit alarm rss in MB', required=True)
    parser.add_argument('-g', '--grep', type=str, help='usage (-g|--grep) process name for grep output ps -eo', required=True)
    parser.add_argument('-n', '--name', type=str, help='usage (-n|--name) process name in monitoring alert', required=True)
    parser.add_argument('-r', '--regexp', type=str, help='usage (-r|--regexp) regexp for ps output', required=True)
    args = parser.parse_args()

    # truncate mon file, need for avoiding overwrite
    try:
        open(args.out, 'w').close()
    except Exception as err:
        print "Error truncate mon file %err" % err
    # write to on file
    if args.grep:
        get_pss_output_Obj = GetPsOutput(args.grep, args.regexp)
        print get_pss_output_Obj.get_process_rss()
        write_mon_file(check_instance_limit(
            get_pss_output_Obj.get_process_rss(),
            convert_string_to_int(args.limit), inst_name=args.name),
            args.out
        )


if __name__ == '__main__':
    main()
