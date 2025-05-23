# MetrANOVA Datastreams

This project provides a Docker Compose setup to run services that collect, process, store, and display aggregated flow data. It also includes tools to register the location of the archives and dynamically build dashboards with the results.

## Summary

The MetrANOVA Datastreams project is designed to facilitate the collection, processing, storage, and visualization of network flow data. It leverages Kafka and Logstash for data processing and includes tools to register archive locations and dynamically generate dashboards.

## Quickstart

### Step 1: Copy env.example to .env
First, copy the env.example file to .env:

```sh
cp env.example .env
```

### Step 2: Update Environment Variables

Edit the .env file to update the necessary environment variables according to your setup. The only required settings are:

 - **MN_HOSTNAME** - The public hostname/IP where Opensearch can be reached
 - **MN_OPENSEARCH_ADMIN_PASSWORD** - The administrator password for opensearch. This password will be created for you when the container starts.
 - **MN_LOGSTASH_OPENSEARCH_PASSWORD** - The password for logtstash will use to authenticate to opensearch. This password will be created for you when the container starts.

### Step 3: Start the Services

To start the services in the Docker Compose collector and archive profiles, run the following command:

```sh
docker-compose --profile collector --profile archive up -d
```
### Step 4: Check Opensearch Dashboards

Open a browser and visit http://YOURHOST/opensearchdash and login with **admin** and the password you set for *MN_OPENSEARCH_ADMIN_PASSWORD* in your .env file. Use the discover panel to view your flow data. You may need to setup a data view to see your data. 

## Using the Docker Compose File

### Starting Different Profiles

The Docker Compose file supports multiple profiles to start different sets of services. Use the following commands to start the desired profiles:

#### Collector Profile

The collector profile runs nfacctd, Kafka and Logstash. To start the collector profile, run:

```sh
docker-compose --profile collector up -d
```

#### Archive Profile

The collector profile runs OpenSearch, OpenSearch Dashboards, psregister (registers Opensearch to the perfSONAR lookup service) and an nginx proxy. The proxy allows you to access Opensearch and Opensearch Dashboards at https://YOURHOST/opensearch and https://YOURHOST/opensearchdash respectively. To start the collector profile, run: To start the archive profile, run:

```sh
docker-compose --profile archive up -d
```

#### Frontend Profile

The frontend profile runs Grafana, Grafana Agent (a tool that queries the perfSONAR lookup service and adds data sources to Grafana) and an nginx proxy. The proxy allows you to access Grafana at https://YOURHOST/. To start the collector profile, run: To start the frontend profile, run:

```sh
docker-compose --frontend archive up -d
```
# Developers

## Useful Kafka Commands

Listen for events on a topic
```
docker compose exec kafka kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic metranova_flow_5m_asn_app
```