#!/bin/bash

###
# Wait for OpenSearch to start
echo "Waiting for opensearch API to start..."
api_status=$(curl -s -o /dev/null -w "%{http_code}" -u admin:${OPENSEARCH_ADMIN_PASSWORD} -k https://${OPENSEARCH_HOST}:${OPENSEARCH_PORT}/_cluster/health)
i=0
while [[ $api_status -ne 200 ]]
do
    sleep 1
    ((i++))
    # Wait a maximum of 100 seconds for the API to start
    if [[ $i -eq 100 ]]; then
        echo "[ERROR] API start timeout"
        exit 1
    fi
    api_status=$(curl -s -o /dev/null -w "%{http_code}" -u admin:${OPENSEARCH_ADMIN_PASSWORD} -k https://${OPENSEARCH_HOST}:${OPENSEARCH_PORT}/_cluster/health)
done
echo "API started!"

##
# Install ISM policy
echo "[Create metranova ISM policy]"
curl -k -u admin:${OPENSEARCH_ADMIN_PASSWORD} -H 'Content-Type: application/json' -X PUT "https://${OPENSEARCH_HOST}:${OPENSEARCH_PORT}/_plugins/_ism/policies/metranova_default" -d "@/usr/src/app/ism.json" 2>/dev/null
echo -e "\n[Applying policy]"
# Apply policy to index
curl -k -u admin:${OPENSEARCH_ADMIN_PASSWORD} -H 'Content-Type: application/json' -X POST "https://${OPENSEARCH_HOST}:${OPENSEARCH_PORT}/_plugins/_ism/add/metranova_*" -d '{ "policy_id": "metranova_default" }' 2>/dev/null
echo -e "\n[DONE]"
echo ""

##
# Install index template
echo "[Create metranova index template]"
curl -k -u admin:${OPENSEARCH_ADMIN_PASSWORD} -s -H 'Content-Type: application/json' -XPUT "https://${OPENSEARCH_HOST}:${OPENSEARCH_PORT}/_index_template/metranova_default" -d @/usr/src/app/index_template.json
echo -e "\n[DONE]"
echo ""

##
# Install anonymous role
echo "[Create metranova_reader role]"
curl -k -u admin:${OPENSEARCH_ADMIN_PASSWORD} -s -H 'Content-Type: application/json' -XPUT "https://${OPENSEARCH_HOST}:${OPENSEARCH_PORT}/_plugins/_security/api/roles/metranova_reader" -d '
{
  "cluster_permissions": [
    "cluster_monitor"
  ],
  "index_permissions": [{
    "index_patterns": [
      "metranova_*"
    ],
    "allowed_actions": [
      "read",
      "indices:admin/mappings/get",
      "indices:monitor/settings/get"
    ]
  }]
}'
echo -e "\n[DONE]"
echo ""

##
# Install anonymous role mapping
echo "[Create role mapping for anonymous user]"
curl -k -u admin:${OPENSEARCH_ADMIN_PASSWORD} -s -H 'Content-Type: application/json' -XPUT "https://${OPENSEARCH_HOST}:${OPENSEARCH_PORT}/_plugins/_security/api/rolesmapping/metranova_reader" -d'
{
  "backend_roles" : [ "opendistro_security_anonymous_backendrole" ]
}'
echo -e "\n[DONE]"
echo ""

##
# Enable anonymous access
echo "[Enable anonymous authentication]"
curl -k -u admin:${OPENSEARCH_ADMIN_PASSWORD} -s -H 'Content-Type: application/json' -XPATCH "https://${OPENSEARCH_HOST}:${OPENSEARCH_PORT}/_plugins/_security/api/securityconfig" -d'
[{
    "op": "add", "path": "/config/dynamic/http/anonymous_auth_enabled", "value": "true"
}]'
echo -e "\n[DONE]"
echo ""

##
# Install metranova_writer role
echo "[Create metranova_writer role]"
curl -k -u admin:${OPENSEARCH_ADMIN_PASSWORD} -s -H 'Content-Type: application/json' -XPUT "https://${OPENSEARCH_HOST}:${OPENSEARCH_PORT}/_plugins/_security/api/roles/metranova_writer" -d '
{
  "cluster_permissions": [
    "cluster_monitor",
    "cluster_manage_index_templates"  
  ],
  "index_permissions": [{
    "index_patterns": [
      "metranova_*"
    ],
    "allowed_actions": [
      "write",
      "read",
      "delete",
      "create_index",
      "manage",
      "indices:admin/template/delete",
      "indices:admin/template/get",
      "indices:admin/template/put"
    ]
  }]
}'
echo -e "\n[DONE]"
echo ""

##
# Install metranova_writer user
echo "[Create metranova_writer user]"
curl -k -u admin:${OPENSEARCH_ADMIN_PASSWORD} -s -H 'Content-Type: application/json' -XPUT "https://${OPENSEARCH_HOST}:${OPENSEARCH_PORT}/_plugins/_security/api/internalusers/metranova_writer" -d "
{
  \"password\": \"${LOGSTASH_OPENSEARCH_PASSWORD}\",
  \"opendistro_security_roles\": [\"metranova_reader\", \"metranova_writer\"]
}"
echo -e "\n[DONE]"
echo ""

##
# Install metranova_writer role mapping
echo "[Create role mapping for metranova_writer user]"
curl -k -u admin:${OPENSEARCH_ADMIN_PASSWORD} -s -H 'Content-Type: application/json' -XPUT "https://${OPENSEARCH_HOST}:${OPENSEARCH_PORT}/_plugins/_security/api/rolesmapping/metranova_writer" -d'
{
  "users" : [ "metranova_writer" ]
}'
echo -e "\n[DONE]"
echo ""