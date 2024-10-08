#!/usr/bin/env python3

##
# Takes a CSV file from IANA and converts to a JSON file we can use for mapping ports to applications
# Also takes a supplemental file that adds/overwrites keys from the offcial list we preferred nams.
# Useful since a lot of common stuff wee see may not be in the list or is mischaracterized.
#
# Input file from: https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.csv
##

import csv
from json import dumps, load
import re

input_filename = "./service-names-port-numbers.csv"
input_filename_supp = "./app_name_supplement.json"
output_directory = "/data/cache"
output_filename_app_names = "{0}/pretag.map.app_names".format(output_directory)

#load file
app_map = []
with open(input_filename, 'r') as f:
    #read line by line
    csvreader = csv.reader(f, delimiter=',')
    i = 0
    #skip header
    next(csvreader)
    for row in csvreader:
        #just to be safe, if file poperly formatted then should not happen
        if len(row) < 3:
            continue
        name = row[0]
        port = row[1]
        proto = row[2]
        if name and port and proto:
            app_map.append([name, port, proto])

#Read supplemental file and add/overwrite official list
with open(input_filename_supp, 'r') as f:
    supp_json = load(f)
    range_pattern = re.compile(r'(.+)\[(\d+)\-(.+)\]')
    for k in supp_json:
        range_match = range_pattern.match(k)
        if range_match:
            for p in range(int(range_match.group(2)), int(range_match.group(3))):
                app_map.append([supp_json[k], p, range_match.group(1)])  
        else:
            no_range_pattern = re.compile(r'(.+)\[(\d+)\]')
            no_range_match = no_range_pattern.match(k)
            if no_range_match:
                app_map.append([supp_json[k], no_range_match.group(2), no_range_match.group(1)])

#output to json file
with open(output_filename_app_names, 'w') as f:
    for app in app_map:
        f.write("set_label={0} dst_port={1} ip_proto={2}\n".format(app[0], app[1], app[2]))
        f.write("set_label={0} src_port={1} ip_proto={2}\n".format(app[0], app[1], app[2]))
