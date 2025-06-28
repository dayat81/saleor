# Google Cloud Live Log Monitoring with gcloud CLI

This guide covers how to use the `gcloud alpha logging tail` command to monitor logs in real-time from Google Cloud services.

## Prerequisites

1. **Install Google Cloud CLI**
   ```bash
   # If not already installed, follow: https://cloud.google.com/sdk/docs/install
   ```

2. **Install Alpha Components**
   ```bash
   gcloud components install alpha
   ```

3. **Install gRPC for Python**
   ```bash
   sudo pip3 install grpcio
   ```

4. **Set Environment Variable**
   ```bash
   export CLOUDSDK_PYTHON_SITEPACKAGES=1
   ```

5. **Configure Project and Auth**
   ```bash
   gcloud config set project PROJECT_ID
   gcloud auth login
   ```

## Basic Usage

### Simple Live Tailing
```bash
# Stream all logs from your project
gcloud alpha logging tail

# Stream logs with a specific filter
gcloud alpha logging tail "resource.type=cloud_run_revision"
```

### Buffer Window
The buffer window (0-60 seconds) controls the delay for ordering logs:
```bash
# No buffering (immediate but potentially out-of-order)
gcloud alpha logging tail --buffer-window=0s

# 10-second buffer (better ordering)
gcloud alpha logging tail --buffer-window=10s
```

## Common Filters

### By Resource Type
```bash
# Cloud Run logs
gcloud alpha logging tail "resource.type=cloud_run_revision"

# Cloud Run Jobs
gcloud alpha logging tail "resource.type=cloud_run_job"

# Cloud Functions
gcloud alpha logging tail "resource.type=cloud_function"

# Compute Engine
gcloud alpha logging tail "resource.type=gce_instance"

# Cloud SQL
gcloud alpha logging tail "resource.type=cloudsql_database"
```

### By Service Name
```bash
# Specific Cloud Run service
gcloud alpha logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=saleor-app"

# Specific Cloud Run job
gcloud alpha logging tail "resource.type=cloud_run_job AND resource.labels.job_name=saleor-migration"
```

### By Severity Level
```bash
# Only errors and above
gcloud alpha logging tail "severity>=ERROR"

# Warnings and above
gcloud alpha logging tail "severity>=WARNING"

# Info level only
gcloud alpha logging tail "severity=INFO"
```

### By Time Range
```bash
# Logs from the last 5 minutes
gcloud alpha logging tail 'timestamp>="2025-06-28T00:00:00Z"'

# Relative time
gcloud alpha logging tail 'timestamp>="-5m"'
```

### By Log Name
```bash
# Specific log name
gcloud alpha logging tail 'logName="projects/PROJECT_ID/logs/run.googleapis.com%2Fstderr"'

# Multiple log names
gcloud alpha logging tail 'logName=~"stderr|stdout"'
```

## Advanced Examples

### Cloud Run Service with Error Filtering
```bash
gcloud alpha logging tail \
  "resource.type=cloud_run_revision AND 
   resource.labels.service_name=saleor-app AND 
   severity>=ERROR"
```

### Cloud Run Job Execution Monitoring
```bash
gcloud alpha logging tail \
  "resource.type=cloud_run_job AND 
   resource.labels.job_name=saleor-migration AND 
   labels.\"run.googleapis.com/execution_name\"=saleor-migration-abc123"
```

### Container Logs with Text Search
```bash
gcloud alpha logging tail \
  "resource.type=cloud_run_revision AND 
   textPayload:\"django.db.utils\""
```

### Multiple Conditions
```bash
gcloud alpha logging tail \
  "resource.type=cloud_run_revision AND 
   resource.labels.service_name=saleor-app AND 
   (severity>=ERROR OR textPayload:\"CRITICAL\")"
```

### Cloud SQL Connection Issues
```bash
gcloud alpha logging tail \
  "resource.type=cloud_run_job AND 
   (textPayload:\"connection refused\" OR 
    textPayload:\"connection timeout\" OR 
    textPayload:\"OperationalError\")"
```

## Practical Examples for Saleor

### Monitor Migration Job
```bash
# Watch migration job execution
gcloud alpha logging tail \
  "resource.type=cloud_run_job AND 
   resource.labels.job_name=~\"saleor-migration\" AND 
   resource.labels.location=us-central1"
```

### Monitor App Deployment
```bash
# Watch service logs during deployment
gcloud alpha logging tail \
  "resource.type=cloud_run_revision AND 
   resource.labels.service_name=saleor-app AND 
   resource.labels.location=us-central1" \
  --buffer-window=5s
```

### Database Connection Debugging
```bash
# Monitor database connection errors
gcloud alpha logging tail \
  "(resource.type=cloud_run_revision OR resource.type=cloud_run_job) AND 
   (textPayload:\"psycopg2\" OR 
    textPayload:\"django.db\" OR 
    textPayload:\"PostgreSQL\")"
```

### Celery Worker Monitoring
```bash
# Monitor Celery worker logs
gcloud alpha logging tail \
  "resource.type=cloud_run_job AND 
   resource.labels.job_name=saleor-worker"
```

## Formatting Options

### JSON Output
```bash
gcloud alpha logging tail --format=json
```

### Custom Format
```bash
gcloud alpha logging tail --format="value(timestamp,severity,textPayload)"
```

### Colorized Output
```bash
gcloud alpha logging tail --format="table(
  timestamp.date('%Y-%m-%d %H:%M:%S'):label=TIME,
  severity:label=LEVEL,
  textPayload:label=MESSAGE
)"
```

## Tips and Best Practices

1. **Use Specific Filters**: Broad filters can overwhelm with too many logs
2. **Set Buffer Window**: Use 5-10 seconds for better log ordering
3. **Monitor Costs**: Live tailing counts against your logging read quota
4. **Combine Filters**: Use AND/OR operators for precise filtering
5. **Save Common Filters**: Store frequently used filters in shell aliases

### Shell Aliases Example
```bash
# Add to ~/.bashrc or ~/.zshrc
alias tail-saleor='gcloud alpha logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=saleor-app"'
alias tail-migration='gcloud alpha logging tail "resource.type=cloud_run_job AND resource.labels.job_name=~\"saleor-migration\""'
alias tail-errors='gcloud alpha logging tail "severity>=ERROR"'
```

## Limitations

- Maximum 60,000 entries per minute
- Maximum 10 concurrent live-tailing sessions per project
- Requires Python 3 with gRPC support
- May show logs out of order without buffer window

## Troubleshooting

### "Command not found" Error
```bash
# Ensure alpha components are installed
gcloud components install alpha
gcloud components update
```

### "ImportError: No module named grpc"
```bash
# Install gRPC and set environment variable
sudo pip3 install grpcio
export CLOUDSDK_PYTHON_SITEPACKAGES=1
```

### No Logs Appearing
1. Check your filter syntax
2. Verify project ID is correct
3. Ensure you have logging.read permissions
4. Try a broader filter to test connectivity