#!/bin/bash

# Script to show current Google Cloud Run jobs and their status
# Usage: ./show_gcloud_jobs.sh [region]

set -e

# Default region
REGION=${1:-us-central1}

echo "=========================================="
echo "Google Cloud Run Jobs Status"
echo "Region: $REGION"
echo "Project: $(gcloud config get-value project)"
echo "=========================================="
echo

# Show all jobs in the region
echo "📋 All Cloud Run Jobs:"
echo "----------------------------------------"
gcloud run jobs list --region=$REGION --format="table(
    metadata.name:label=JOB_NAME,
    status.conditions[0].type:label=STATUS,
    status.latestCreatedExecution.name:label=LATEST_EXECUTION,
    status.latestCreatedExecution.createTime:label=CREATED,
    spec.template.spec.template.spec.containers[0].image:label=IMAGE
)"

echo
echo "🔄 Recent Job Executions:"
echo "----------------------------------------"
# Get executions for each job
for job in $(gcloud run jobs list --region=$REGION --format="value(metadata.name)"); do
    echo "Job: $job"
    gcloud run jobs executions list --job=$job --region=$REGION --limit=3 --format="table(
        metadata.name:label=EXECUTION_ID,
        status.conditions[0].type:label=STATUS,
        status.startTime:label=START_TIME,
        status.completionTime:label=COMPLETION_TIME
    )" 2>/dev/null || echo "  No executions found"
    echo
done

echo "🔗 Useful Commands:"
echo "----------------------------------------"
echo "View job details:     gcloud run jobs describe JOB_NAME --region=$REGION"
echo "Execute a job:        gcloud run jobs execute JOB_NAME --region=$REGION"
echo "View execution logs:  gcloud logging read 'resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME' --limit=50 --format='table(timestamp,textPayload)'"
echo "Monitor live logs:    ./monitor_logs.sh JOB_NAME"
echo
echo "📊 For detailed monitoring, check: https://console.cloud.google.com/run/jobs?project=$(gcloud config get-value project)"