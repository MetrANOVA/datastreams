#!/usr/bin/env python3

import os
import elasticsearch
import logging
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import time

#Global settings
urllib3.disable_warnings()
logger = logging.getLogger(__name__)
# create basic logger
logging.basicConfig(level=logging.INFO)
DEFAULT_GRAFANA_DS_SETTINGS = {
    "type": "grafana-opensearch-datasource", 
    "url": None, #to be overwritten 
    "user": "", 
    "database": "", 
    "basicAuth": False, 
    "isDefault": False, 
    "access": "proxy",
    "jsonData": {
        "database": "metranova_*", 
        "flavor": "opensearch", 
        "maxConcurrentShardRequests": 5, 
        "pplEnabled": True, 
        "timeField": "start", 
        "tlsAuth": False, 
        "tlsSkipVerify": True,
        "version": "AUTO"
    }, 
    "readOnly": False
}

##
# Subroutines
def gf_build_url(grafana_url, path):
    '''
    Builds a URL for the Grafana API
    '''
    return "{}{}".format(grafana_url.strip().rstrip('/'), path)

def gf_http(url, action, method="get", data={}, headers={}, auth=None, log_prefix="", timeout=5):
    '''
    General function for sending HTTP requests and handling errors
    '''
    local_context = {}
    local_context["{}url".format(log_prefix)] = url
    local_context["action"] = "{}.start".format(action)
    if data:
        local_context["data"] = data
    logger.debug(local_context)
    r = None
    msg=None
    try:
        r = None
        if method == "get":
            r = requests.get(url, headers=headers, auth=auth, verify=False, timeout=timeout)
        elif method == "post":
            print(auth)
            r = requests.post(url, json=data, headers=headers, auth=auth, verify=False, timeout=timeout)
        elif method == "put":
            r = requests.put(url, json=data, headers=headers, auth=auth, verify=False, timeout=timeout)
        elif method == "patch":
            r = requests.patch(url, json=data, headers=headers, auth=auth, verify=False, timeout=timeout)
        elif method == "delete":
            r = requests.delete(url, headers=headers, auth=auth, verify=False, timeout=timeout)
        else:
            return None, "Invalid method specified."
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        msg="HTTP Error - {}".format(err)
    except requests.exceptions.Timeout as err:
        msg="Timeout Error - {}".format(err)
    except requests.exceptions.RequestException as err:
        msg="Request Error - {}".format(err)
    except:
        msg="General exception trying to contact {}".format(url)
    
    #log depending on if we got an error
    if msg:
        local_context["action"] = "{}.error".format(action)
        logger.error(msg, local_context)
    else:
        local_context["action"] = "{}.end".format(action)
        try:
            local_context["response"] = r.json()
        except:
            pass
        logger.debug(local_context)

    return r, msg

##
# Tests grafana request and returns error message if a problem occurs
def gf_test_connection(gf_url, gf_auth, gf_header):
    '''
    Tests connection to Grafana by reaching out to the organization API
    '''
    ep_url = gf_build_url(gf_url, '/api/org')
    r, msg = gf_http(ep_url, "grafana_test", headers=gf_header, auth=gf_auth)

    return msg

def gf_list_datasources_by_name(gf_url, gf_auth, gf_header):
    '''
    Retrieves list of datasources from Grafana API and organizes 
    into dictionary where key is the datasource name and value is 
    an object with datasource type and uid
    '''
    ep_url = gf_build_url(gf_url, '/api/datasources')
    r, msg = gf_http(ep_url, "list_datasources", headers=gf_header, auth=gf_auth)
    if msg or not r:
        return {}
    ds_list = r.json()
    if not isinstance(ds_list, list):
        return {}
    ds_by_name = {}
    for ds in ds_list:
        if ds.get("name", None) and ds.get("type", None) and ds.get("uid", None):
            ds_by_name[ds["name"]] = {
                "type": ds["type"],
                "uid": ds["uid"],
            }

    return ds_by_name

##
# Build a grafana data source for the given url
def build_grafana_datasource(url, datasources, gf_url, gf_auth, gf_header):
    #init settings
    ds_settings = DEFAULT_GRAFANA_DS_SETTINGS.copy()
    ds_settings["url"] = url
    ds_settings["name"] = "MetrANOVA - {}".format(url)

    # get opensearch version
    #fetch version
    r, msg = gf_http(url, "ds_version", log_prefix="ds_")
    if msg:
        #return if error making request
        return

    #parse version
    ds_settings["jsonData"]["version"] = r.json().get("version", {}).get("number", None)
    if ds_settings["jsonData"]["version"] is None:
        logger.error("Unable to determine version for opensearch {}".format(url))
        return

    # determine action
    r = None
    msg = None
    if datasources.get(ds_settings["name"], None):
        #if datasource exists then update
        logger.info("Updating datasource for {}".format(url))
        ds_settings["uid"] = datasources[ds_settings["name"]].get("uid", None)
        if ds_settings["uid"] is None:
            logger.error("Unable to find uid for datasource {}".format(url))
            return {}
        ep_url = gf_build_url(gf_url, '/api/datasources/uid/{}'.format(ds_settings["uid"]))
        r, msg = gf_http(ep_url, "update_datasource", method="put", data=ds_settings, headers=gf_header, auth=gf_auth)
        if msg:
            logger.error("Unable to update datasource for {}: {}".format(url, msg))
            return {}
    else:
        #else create new datasource
        logger.info("Creating new datasource for {}".format(url))
        ep_url = gf_build_url(gf_url, '/api/datasources')
        r, msg = gf_http(ep_url, "create_datasource", method="post", data=ds_settings, headers=gf_header, auth=gf_auth)
        if msg:
            logger.error("Unable to create datasource for {}: {}".format(url, msg))
            return {}
    
    #parse response of update or create
    uid = r.json().get("datasource", {}).get("uid", None)
    ds_type = r.json().get("datasource", {}).get("type", None)
    if uid and ds_type:
        datasources[ds_settings["name"]] = {
            "type": ds_type,
            "uid": uid
        }
        return datasources[ds_settings["name"]]
    else:
        logger.error("Something went wrong with datasource for {}. Unable to find uid.".format(url))

    return {}

def main():
    # get check_interval from environment var CHECK_INTERVAL, default to 5 minutes
    check_interval = int(os.environ.get('CHECK_INTERVAL', 300))

    # get the elastic url from environment var LOOKUP_SERVICE_ES_URL
    es_url = os.environ.get('LOOKUP_SERVICE_ES_URL', None)
    if es_url is None:
        print("LOOKUP_SERVICE_ES_URL is not set")
        exit(1)

    # get the elastic index from environment var LOOKUP_SERVICE_ES_INDEX
    es_index = os.environ.get('LOOKUP_SERVICE_ES_INDEX', None)
    if es_index is None:
        print("LOOKUP_SERVICE_ES_INDEX is not set")
        exit(1)

    # get the elastic user from environment var LOOKUP_SERVICE_ES_USER
    es_user = os.environ.get('LOOKUP_SERVICE_ES_USER', None)
    if es_user is None:
        print("LOOKUP_SERVICE_ES_USER is not set")
        exit(1)

    # get the elastic password from environment var LOOKUP_SERVICE_ES_PASS
    es_pass = os.environ.get('LOOKUP_SERVICE_ES_PASS', None)
    if es_pass is None:
        print("LOOKUP_SERVICE_ES_PASS is not set")
        exit(1)

    # get the grafana url from environment var GRAFANA_URL
    gf_url = os.environ.get('GRAFANA_URL', None)
    if gf_url is None:
        print("GRAFANA_URL is not set")
        exit(1)
    
    # get the grafana user from environment var GRAFANA_USER
    gf_user = os.environ.get('GRAFANA_USER', None)
    if gf_user is None:
        print("GRAFANA_USER is not set")
        exit(1)
    
    # get the grafana password from environment var GRAFANA_PASSWORD
    gf_pass = os.environ.get('GRAFANA_PASSWORD', None)
    if gf_pass is None:
        print("GRAFANA_PASSWORD is not set")
        exit(1)

    # build grafana auth header
    gf_auth = HTTPBasicAuth(gf_user, gf_pass)
    gf_header = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    ############################################
    # Test connection to grafana
    msg = gf_test_connection(gf_url, gf_auth, gf_header)
    if msg:
        print("Error testing connection to Grafana: {}".format(msg))
        exit(1)

    # infinite loop to keep the agent running
    while True:
        try:
            logger.info("Checking for new archives")
            ############################################
            # get list of data sources from grafana
            gf_datasources = gf_list_datasources_by_name(gf_url, gf_auth, gf_header)
            logger.debug("Datasources: {}".format(gf_datasources))

            ##################################################
            # query elastic search to get the list of archives
            es = elasticsearch.Elasticsearch([es_url], basic_auth=(es_user, es_pass), verify_certs=False)
            res = es.search(index=es_index, body={"query": {"match_all": {}}})
            print("Got %d Hits" % res['hits']['total']['value'])
            for hit in res['hits']['hits']:
                urls = hit.get("_source", {}).get("host", {}).get("archive_service", {}).get("urls", [])
                if len(urls) > 0:
                    build_grafana_datasource(urls[0], gf_datasources, gf_url, gf_auth, gf_header)
        except:
            logger.error("Error in main loop", exc_info=True)

        # sleep for 5 minutes
        logger.info("Sleeping for {} seconds".format(check_interval))
        time.sleep(check_interval)

# Run the main function
if __name__ == "__main__":
    main()