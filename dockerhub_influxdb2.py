#! /usr/bin/python

# Script originally created by JON HAYWARD: https://fattylewis.com/Graphing-pi-hole-stats/
# Adapted to work with InfluxDB by /u/tollsjo in December 2016
# Updated by Cludch December 2016
# Updated and dockerised by rarosalion in September 2019
# Updated by Dick Pluim December 2022 and modified to use with Dockerhub 

# To install and run the script as a service under SystemD. See: https://linuxconfig.org/how-to-automatically-execute-shell-script-at-startup-boot-on-systemd-linux

import requests
import time
import json
import os
import logging
from influxdb_client import InfluxDBClient, BucketRetentionRules
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS

# Modify these values if running as a standalone script
_DEFAULTS = {
    'INFLUXDB_V2_URL': "10.0.0.10:8087",  # URL to InfluxDB server
    'INFLUXDB_V2_TOKEN': "",  # Token from INFLUX_TOKEN
    'INFLUXDB_V2_ORG': "my-org",  # Default org
    'DELAY': 60,  # seconds
    'INFLUXDB_BUCKET': "dockerhub/autogen", # default bucket
    'DOCKERHUB_IMAGES': [],  # Dockerhub images 
    'DOCKERHUB_USERS': [],  # Dockerhub users 
}


def get_config():
    """ Combines config options from config.json file and environment variables """

    # Read a config file (json dictionary) if it exists in the script folder
    script_dir = os.path.dirname(os.path.realpath(__file__))
    config_file = os.path.join(script_dir, 'config.json')
    if os.path.exists(config_file):
        config = json.load(open(config_file))
    else:
        config = _DEFAULTS

    # Overwrite config with environment variables (set via Docker)
    for var_name in _DEFAULTS.keys():
        config[var_name] = os.getenv(var_name, _DEFAULTS[var_name])
        if var_name == 'DOCKERHUB_IMAGES' and ',' in config[var_name]:
            config[var_name] = config[var_name].split(',')

        if var_name == 'DOCKERHUB_USERS' and ',' in config[var_name]:
            config[var_name] = config[var_name].split(',')

    # Make sure DOCKERHUB_IMAGES is a list (even if it's just one entry)
    if not isinstance(config['DOCKERHUB_IMAGES'], list):
        config['DOCKERHUB_IMAGES'] = [config['DOCKERHUB_IMAGES']]

    # Make sure DOCKERHUB_USERS is a list (even if it's just one entry)
    if not isinstance(config['DOCKERHUB_USERS'], list):
        config['DOCKERHUB_USERS'] = [config['DOCKERHUB_USERS']]

    return config


def check_bucket_status(config, logger):
    """ Check the required bucket exists, and create it if necessary """

    logger.debug("Connecting to {}".format(config['INFLUXDB_V2_URL']))
    client = InfluxDBClient(
        url = config['INFLUXDB_V2_URL'],
        token = config['INFLUXDB_V2_TOKEN'],
        org = config['INFLUXDB_V2_ORG']
    )
    buckets_api = client.buckets_api()
    buckets = buckets_api.find_buckets().buckets
    i = 0
    bucket_name = []
    for bucket in buckets:
         bucket_name.append(bucket.name)
#         print(bucket_name[i], len(bucket_name[i]))
         i = i + 1
#    print (config['INFLUXDB_BUCKET'], len(config['INFLUXDB_BUCKET']))
#    print (bucket_name.index(config['INFLUXDB_BUCKET']))

    if config['INFLUXDB_BUCKET'] not in bucket_name:
        logger.info('Bucket {} not found. Will attempt to create it.'.format(config['INFLUXDB_BUCKET']))
        retention_rules=BucketRetentionRules(type="expire", every_seconds=0)
        created_bucket = buckets_api.create_bucket(bucket_name=config['INFLUXDB_BUCKET'],org=config['INFLUXDB_V2_ORG'])
#        client.create_bucket(config['INFLUXDB_BUCKET'])
        return True
    else:       
        logger.info('Found existing bucket {}.'.format(config['INFLUXDB_BUCKET']))
        return True


def send_msg(config, logger, image, user, name, pull_count, star_count, last_updated, status):
    """ Sends message to InfluxDB server defined in config """
    write_options="SYNCHROUNOUS"
    json_body = [
        { 
            "measurement": "dockerhubstats." + image.replace(".", "_"),
            "tags": {
                "image": image 
            },
            "fields": {
                "user": user,
                "name": name,
                "pull_count": int(pull_count),
                "star_count": int(star_count),
                "last_updated": last_updated,
                "status": status
            }
        }
    ]
    logger.debug(json_body)

    # InfluxDB host, InfluxDB port, Username, Password, database
    client = InfluxDBClient(
        url = config['INFLUXDB_V2_URL'],
        token = config['INFLUXDB_V2_TOKEN'],
        org = config['INFLUXDB_V2_ORG']
    )
   # write_api.write(bucket=config['INFLUXDB_BUCKET', json_body])
 
    client.write_api(write_options=SYNCHRONOUS).write(bucket=config['INFLUXDB_BUCKET'], record=json_body)
   # client.write_api(json_body)
   # print(json_body)


if __name__ == '__main__':

    # Setup logger
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])

    # Get configuration details
    config = get_config()
    number_of_users = len(config['DOCKERHUB_USERS']) 
    number_of_images = len(config['DOCKERHUB_IMAGES'])

    logger.info("Querying {} dockerhub users: {}".format(len(config['DOCKERHUB_USERS']), config['DOCKERHUB_USERS']))
    logger.info("Querying {} dockerhub images: {}".format(len(config['DOCKERHUB_IMAGES']), config['DOCKERHUB_IMAGES']))
    logger.info("Logging to InfluxDB server {}".format(
        config['INFLUXDB_V2_URL'] 
    ))

    # Create database if it doesn't exist
    check_bucket_status(config, logger)
    
    # Loop pulling stats from dockerhub, and pushing to influxdb
    while True:
        # loop through users
        i = 0
        for i in range(number_of_users):
            user = config['DOCKERHUB_USERS'][i]
            # Get Dockerhub Stats
            dockerhub_api = "https://hub.docker.com/v2/repositories/{}".format(user)
            logger.info("Attemping to contact {} with URL {}".format(user, dockerhub_api))
            api = requests.get(dockerhub_api)  # URI to dockerhub server api
#            logger.info("API-result: {}".format(api))
            API_out = api.json()
            count = (API_out['count'])
#            logger.info("count: {}".format(count))
            results = (API_out['results'])
            j = 0 
            for j in range(count):
#                logger.debug("result {}: {}".format(j, results[j]))

                # Get Dockerhub Stats per image
                user = results[j]['namespace'] 
                image = user + "/" + results[j]['name'] 
                name = results[j]['name']
                pull_count = results[j]['pull_count']
                star_count = results[j]['star_count']
                last_updated = results[j]['last_updated']
                status = results[j]['status']
                # Update DB
                send_msg(config, logger, image, user, name, pull_count, star_count, last_updated, status)
                j = j + 1

        i = i + 1

        i = 0
        for i in range(number_of_images): 
            image = config['DOCKERHUB_IMAGES'][i]
            # Get Dockerhub Stats
            dockerhub_api = "https://hub.docker.com/v2/repositories/{}".format(image)
            logger.info("Attempting to contact {} with URL {}".format(image, dockerhub_api))
            api = requests.get(dockerhub_api)  # URI to dockerhub server api
            print (api)
            API_out = api.json()
            user = (API_out['user'])
            name = (API_out['name'])
            pull_count = (API_out['pull_count'])
            print ("Pull count ", pull_count)
            star_count = (API_out['star_count'])
            last_updated = (API_out['last_updated'])
            status = (API_out['status'])

            # Update DB
            send_msg(config, logger, image, user, name, pull_count, star_count, last_updated, status)
            i = i + 1

        # Wait...
        logger.info("Waiting {}".format(config['DELAY']))
        time.sleep(int(config['DELAY']))
