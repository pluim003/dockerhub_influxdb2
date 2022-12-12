## Dockerhub_Influx

A basic script for inserting dockerhub data into influxdb for graphing.

*dockerhub_influxdb2.py* - A python script for inserting records into influxdb (2.x-version).

If you need the version for InfluxDB 1.x, visit https://github.com/pluim003/dockerhub_influx 

Configuration options:
``` bash
INFLUXDB_V2_URL = "127.0.0.1:8086" # IP or hostname to InfluxDB server with port
INFLUXDB_V2_TOKEN = "<token>" # INFLUXDB-token (can be optained by using the value for INFLUX_TOKEN in your influx-confi
INFLUXDB_V2_ORG = "my-org" # Organization to be used
INFLUXDB_BUCKET = "dockerhub"
DELAY = 600 # seconds
DELAY = 600 # seconds
DOCKERHUB_IMAGES = "ubuntu/nginx" # Dockerhub image(s) to report in InfluxDB for each measurement. Comma separated list.
DOCKERHUB_USERS = "pluim003" # Dockerhub user(s) to report in InfluxDB. The script will scan all images owned by this user and report in InfluxDB for each measurement. Comma separated list.
```
*docker-compose.yml* - An example Docker setup to run this script

Configuration options above can be specified within the environment section of the compose file.
You can use both options, or you can leave one of those options empty, e.g. commenting out f.e. DOCKERHUB_USERS if you want only to get statistics of specific images. To report statistics from all images by a specific users it's wise to use the environment variable DOCKERHUB_USERS.

Run:

Create a subdirectory for your installation
Create and edit docker-compose.yml to your needs

``` bash
docker-compose up -d
```

Configuration options above can be specified within the environment section of the compose file.

dockerhub-influx.service - A SystemD Unit File for starting dockerhub_influx at boot (and logging) On Centos7, put this file in /lib/systemd/system/.

Run:

systemctl daemon-reload
systemctl enable dockerhub-influx
systemctl start dockerhub-influx

To run dockerhub_influxdb2.py from the command line without the startup script:
```bash
/usr/bin/python ./dockerhub_influxdb2.py
```

I only use the docker-variant.
You could instal this script in /opt/dockerhub_influx. If you put it somewhere else you'll have to update the systemD startup script.

### Note

I have only tested this script to export to InfluxDB v2.5.1. I'm running a container with Influxdb 2.5.1 and latest versions of Grafana and Telegraf. I expect it will work with all InfluxDB v2.x-releases but if you encounter issues with earlier releases feel free to file an issue.

### Troubleshooting

If you get the following error:

Traceback (most recent call last): File "./dockerhub_influxdb2.py", line 11, in <module> from influxdb import InfluxDBClient

You'll need to install the python-influxdb module for python. On a raspberry pi, you can do this with:

sudo apt-get install python-influxdb

Or on CentOS / RHEL:

yum install python-influxdb

If you get this error:

Traceback (most recent call last): File "./dockerhub_influxdb2.py", line 8, in <module> import requests ImportError: No module named requests

You'll need to install the python-requests module.

### Credits

Credits go to https://github.com/chrisbergeron/ for supplying the pihole_influx-script. After some modifications earlier I decided to make it suitable to get Dockerhub-statistics and now upgraded to InfluxDB 2.x.

### Background

I used the docker-hub-exporter for a while which exports data to a Promotheus-database. Created by https://github.com/badsmoke . But didn't like the way stuff was stored and with zero knowledge of golang I couldn't get it the way I wanted it.

