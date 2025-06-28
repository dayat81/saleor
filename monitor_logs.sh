#!/bin/bash

# Live Log Monitoring Script for Saleor
# Usage: ./monitor_logs.sh [filter_type]

set -e

PROJECT_ID="melodic-now-463704-k1"
REFRESH_INTERVAL=5  # seconds

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Saleor Live Log Monitor${NC}"
echo -e "${BLUE}Project: ${PROJECT_ID}${NC}"
echo "Refreshing every ${REFRESH_INTERVAL} seconds. Press Ctrl+C to stop."
echo "----------------------------------------"

# Function to get timestamp for freshness filter
get_timestamp() {
    date -u -d "${REFRESH_INTERVAL} seconds ago" '+%Y-%m-%dT%H:%M:%SZ'
}

# Different monitoring modes
case "${1:-all}" in
    "migration"|"migrate")
        echo -e "${YELLOW}📊 Monitoring Migration Jobs${NC}"
        FILTER="resource.type=cloud_run_job AND resource.labels.job_name=~\"saleor-migration\""
        ;;
    "app"|"service")
        echo -e "${YELLOW}🚀 Monitoring App Service${NC}"
        FILTER="resource.type=cloud_run_revision AND resource.labels.service_name=saleor-app"
        ;;
    "worker")
        echo -e "${YELLOW}⚙️ Monitoring Worker Jobs${NC}"
        FILTER="resource.type=cloud_run_job AND resource.labels.job_name=saleor-worker"
        ;;
    "errors")
        echo -e "${YELLOW}❌ Monitoring Errors Only${NC}"
        FILTER="severity>=ERROR"
        ;;
    "database"|"db")
        echo -e "${YELLOW}🗄️ Monitoring Database Issues${NC}"
        FILTER="textPayload:(\"connection\" OR \"database\" OR \"psycopg\" OR \"django.db\" OR \"OperationalError\")"
        ;;
    *)
        echo -e "${YELLOW}📋 Monitoring All Cloud Run Logs${NC}"
        FILTER="resource.type=cloud_run_job OR resource.type=cloud_run_revision"
        ;;
esac

echo "Filter: ${FILTER}"
echo "----------------------------------------"

# Store last seen timestamp
LAST_TIMESTAMP=""

while true; do
    # Get current timestamp for freshness
    FRESHNESS_TIME=$(get_timestamp)
    
    # Build the gcloud command
    CMD="gcloud logging read \"${FILTER}\""
    
    # Add timestamp filter if we have a last seen timestamp
    if [ -n "$LAST_TIMESTAMP" ]; then
        CMD="${CMD} AND timestamp>=\"${LAST_TIMESTAMP}\""
    fi
    
    CMD="${CMD} --limit=50 --format=\"table(timestamp.date('%H:%M:%S'),severity,resource.type.yesno(no=''):label=TYPE,textPayload.yesno(no=''):label=MESSAGE)\" --freshness=1m"
    
    # Execute command and capture output
    OUTPUT=$(eval "$CMD" 2>/dev/null | tail -n +2)  # Skip header row
    
    if [ -n "$OUTPUT" ]; then
        # Color code the output based on severity
        echo "$OUTPUT" | while IFS= read -r line; do
            if [[ "$line" == *"ERROR"* ]]; then
                echo -e "${RED}$line${NC}"
            elif [[ "$line" == *"WARNING"* ]]; then
                echo -e "${YELLOW}$line${NC}"
            elif [[ "$line" == *"INFO"* ]]; then
                echo -e "${GREEN}$line${NC}"
            else
                echo "$line"
            fi
        done
        
        # Update last timestamp
        LAST_TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
        echo -e "${BLUE}--- $(date) ---${NC}"
    else
        echo -n "."
    fi
    
    sleep $REFRESH_INTERVAL
done