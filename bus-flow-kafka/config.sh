#!/bin/bash

# set KAFKA_RENTENTION_MS to value of MN_KAFKA_RENTENTION_MS or default to 86400000
KAFKA_RENTENTION_MS=${MN_KAFKA_RENTENTION_MS:-86400000}
# set KAFKA_RENTENTION_BYTES to value of MN_KAFKA_RENTENTION_BYTES or default to 5000000000
KAFKA_RENTENTION_BYTES=${MN_KAFKA_RENTENTION_BYTES:-5000000000}

# Waiting for kafka to start
echo "Waiting for kafka to start..."
i=0
while [[ $(kafka-topics.sh --list --bootstrap-server kafka:9092 > /dev/null; echo $?) -ne 0 ]]
do
    sleep 1
    ((i++))
    # Wait a maximum of 100 seconds for the API to start
    if [[ $i -eq 100 ]]; then
        echo "[ERROR] Kafka start timeout"
        exit 1
    fi
done
echo "Kafka started!"

# Create/alter topic
echo "Creating/altering topic metranova_flow with retention.ms=${KAFKA_RENTENTION_MS} and retention.bytes=${KAFKA_RENTENTION_BYTES}"
kafka-topics.sh --create --bootstrap-server kafka:9092 --if-not-exists --topic metranova_flow --config retention.ms=${KAFKA_RENTENTION_MS} --config retention.bytes=${KAFKA_RENTENTION_BYTES}
kafka-configs.sh --alter --bootstrap-server kafka:9092 --entity-type topics --entity-name  metranova_flow --add-config retention.ms=${KAFKA_RENTENTION_MS} 
kafka-configs.sh --alter --bootstrap-server kafka:9092 --entity-type topics --entity-name  metranova_flow --add-config retention.bytes=${KAFKA_RENTENTION_BYTES}
echo "[DONE]"