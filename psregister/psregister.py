#!/usr/bin/env python3

import os
import requests
import uuid
import ipaddress
import socket
import urllib3
urllib3.disable_warnings()

"""
psregister.py

Description: Registers archive to perfSONAR lookup service
"""

# Get the lookup service URL from the environment
ls_url = os.environ.get('LOOKUP_SERVICE_URL', None)
if ls_url is None:
    #exit if LOOKUP_SERVICE_URL is not set
    print("LOOKUP_SERVICE_URL is not set")
    exit(1)
ls_url = ls_url.removesuffix("/") + "/record/"

#get the hostname from the environment
hostname = os.environ.get('HOSTNAME', None)
if hostname is None:
    #exit if HOSTNAME is not set
    print("HOSTNAME is not set")
    exit(1)
elif hostname == "localhost":
    print("WARN: Not registering localhost")
    exit(0)

#get the archive URL from the environment
archive_url = os.environ.get('ARCHIVE_URL', None)   
if archive_url is None:
    #exit if ARCHIVE_URL is not set
    print("ARCHIVE_URL is not set")
    exit(1)

# generate uuid based on hostname
client_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, hostname))

host_ip = hostname
addresses = set()
try:
    ipaddress.ip_address(host_ip)
    addresses.add(host_ip)
except ValueError:
    # Get both IPv4 and IPv6 addresses
    try:
        addrs = socket.getaddrinfo(hostname, None)
        for addr in addrs:
            if(addr[0] == socket.AF_INET or addr[0] == socket.AF_INET6):
                addresses.add(addr[4][0])
    except socket.gaierror:
        print("Unable to find IP address for hostname: {}".format(hostname))
        exit(1)

# Use requests to send http post to ls_url to register the archive
print("Registering archive with lookup service at {}".format(ls_url))
data={
   "name":"mn",
   "addresses": list(addresses),
   "host":{
      "client_uuid": client_uuid,
      "archive_service":{
         "urls":[
            archive_url
         ],
         "archiver_type":"metranova:opensearch"
      },
      "name":[ hostname]
   }
}
print("Registering {}".format(data))
# Send the request and skip SSL verification
r = requests.post(ls_url, json=data, verify=False)
r.raise_for_status()
print("Registration successful")


