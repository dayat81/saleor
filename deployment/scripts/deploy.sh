#!/bin/bash
# Saleor Google Cloud Deployment Script
# This script automates the deployment of Saleor to Google Cloud Platform

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID=""
REGION="us-central1"
ENVIRONMENT="production"
IMAGE_TAG="latest"
TERRAFORM_DIR="infrastructure"
SKIP_TERRAFORM=false
SKIP_BUILD=false
SKIP_MIGRATION=false
DRY_RUN=false

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Saleor Google Cloud Deployment Script

Usage: $0 [OPTIONS]

Required:
  -p, --project-id PROJECT_ID    Google Cloud Project ID

Options:
  -r, --region REGION           Google Cloud region (default: us-central1)
  -e, --environment ENV         Environment name (default: production)
  -t, --tag TAG                 Docker image tag (default: latest)
  --terraform-dir DIR           Terraform directory (default: infrastructure)
  --skip-terraform              Skip Terraform deployment
  --skip-build                  Skip Docker image build
  --skip-migration              Skip database migration
  --dry-run                     Show what would be done without executing
  -h, --help                    Show this help message

Examples:
  $0 -p my-project-id
  $0 -p my-project-id -e staging -t v1.2.3
  $0 -p my-project-id --skip-terraform --skip-build
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--project-id)
                PROJECT_ID="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -t|--tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            --terraform-dir)
                TERRAFORM_DIR="$2"
                shift 2
                ;;
            --skip-terraform)
                SKIP_TERRAFORM=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-migration)
                SKIP_MIGRATION=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Validate required arguments
    if [[ -z "$PROJECT_ID" ]]; then
        log_error "Project ID is required. Use -p or --project-id"
        show_help
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if gcloud is installed and authenticated
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi

    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi

    # Check if terraform is installed (if not skipping)
    if [[ "$SKIP_TERRAFORM" == false ]] && ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Please install it first."
        exit 1
    fi

    # Check gcloud authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 &> /dev/null; then
        log_error "Not authenticated with gcloud. Run 'gcloud auth login' first."
        exit 1
    fi

    # Set gcloud project
    if [[ "$DRY_RUN" == false ]]; then
        gcloud config set project "$PROJECT_ID"
    fi

    log_success "Prerequisites check passed"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    if [[ "$SKIP_TERRAFORM" == true ]]; then
        log_info "Skipping Terraform deployment"
        return
    fi

    log_info "Deploying infrastructure with Terraform..."

    if [[ ! -d "$TERRAFORM_DIR" ]]; then
        log_error "Terraform directory '$TERRAFORM_DIR' does not exist"
        exit 1
    fi

    cd "$TERRAFORM_DIR"

    # Check if terraform.tfvars exists
    if [[ ! -f "terraform.tfvars" ]]; then
        log_warning "terraform.tfvars not found. Using terraform.tfvars.example as template"
        if [[ -f "terraform.tfvars.example" ]]; then
            cp terraform.tfvars.example terraform.tfvars
            log_warning "Please edit terraform.tfvars with your configuration"
            exit 1
        fi
    fi

    if [[ "$DRY_RUN" == false ]]; then
        # Initialize Terraform
        terraform init

        # Plan deployment
        terraform plan -var="project_id=$PROJECT_ID" -var="environment=$ENVIRONMENT"

        # Apply deployment
        terraform apply -var="project_id=$PROJECT_ID" -var="environment=$ENVIRONMENT" -auto-approve
    else
        log_info "[DRY RUN] Would run: terraform apply -var='project_id=$PROJECT_ID' -var='environment=$ENVIRONMENT'"
    fi

    cd - > /dev/null

    log_success "Infrastructure deployment completed"
}

# Build and push Docker images
build_and_push_images() {
    if [[ "$SKIP_BUILD" == true ]]; then
        log_info "Skipping Docker image build"
        return
    fi

    log_info "Building and pushing Docker images..."

    # Get Artifact Registry repository URL
    REPO_URL="$REGION-docker.pkg.dev/$PROJECT_ID/saleor"

    # Configure Docker for Artifact Registry
    if [[ "$DRY_RUN" == false ]]; then
        gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet
    fi

    # Build main application image
    log_info "Building main application image..."
    if [[ "$DRY_RUN" == false ]]; then
        docker build -f Dockerfile.cloudrun -t "$REPO_URL/saleor:$IMAGE_TAG" .
        docker push "$REPO_URL/saleor:$IMAGE_TAG"
    else
        log_info "[DRY RUN] Would build and push: $REPO_URL/saleor:$IMAGE_TAG"
    fi

    # Build worker image
    log_info "Building worker image..."
    if [[ "$DRY_RUN" == false ]]; then
        docker build -f Dockerfile.worker -t "$REPO_URL/saleor-worker:$IMAGE_TAG" .
        docker push "$REPO_URL/saleor-worker:$IMAGE_TAG"
    else
        log_info "[DRY RUN] Would build and push: $REPO_URL/saleor-worker:$IMAGE_TAG"
    fi

    log_success "Docker images built and pushed successfully"
}

# Deploy to Cloud Run
deploy_cloud_run() {
    log_info "Deploying to Cloud Run..."

    # Get service name (assuming it follows the pattern)
    SERVICE_NAME="saleor-app"
    WORKER_JOB_NAME="saleor-worker"

    # Update Cloud Run service
    if [[ "$DRY_RUN" == false ]]; then
        gcloud run deploy "$SERVICE_NAME" \
            --image="$REGION-docker.pkg.dev/$PROJECT_ID/saleor/saleor:$IMAGE_TAG" \
            --region="$REGION" \
            --platform=managed \
            --allow-unauthenticated \
            --memory=2Gi \
            --cpu=2 \
            --timeout=900 \
            --max-instances=100 \
            --concurrency=200 \
            --set-env-vars="ENVIRONMENT=$ENVIRONMENT" \
            --quiet
    else
        log_info "[DRY RUN] Would deploy Cloud Run service: $SERVICE_NAME"
    fi

    # Update Cloud Run job for workers
    if [[ "$DRY_RUN" == false ]]; then
        gcloud run jobs replace-job \
            --image="$REGION-docker.pkg.dev/$PROJECT_ID/saleor/saleor-worker:$IMAGE_TAG" \
            --region="$REGION" \
            --memory=1Gi \
            --cpu=1 \
            --parallelism=10 \
            --set-env-vars="ENVIRONMENT=$ENVIRONMENT" \
            "$WORKER_JOB_NAME" \
            --quiet || log_warning "Worker job update failed - it may not exist yet"
    else
        log_info "[DRY RUN] Would update Cloud Run job: $WORKER_JOB_NAME"
    fi

    log_success "Cloud Run deployment completed"
}

# Run database migrations
run_migrations() {
    if [[ "$SKIP_MIGRATION" == true ]]; then
        log_info "Skipping database migration"
        return
    fi

    log_info "Running database migrations..."

    # Create a temporary Cloud Run job for migrations
    MIGRATION_JOB_NAME="saleor-migration-$(date +%s)"

    if [[ "$DRY_RUN" == false ]]; then
        # Create migration job
        gcloud run jobs create "$MIGRATION_JOB_NAME" \
            --image="$REGION-docker.pkg.dev/$PROJECT_ID/saleor/saleor:$IMAGE_TAG" \
            --region="$REGION" \
            --memory=1Gi \
            --cpu=1 \
            --task-count=1 \
            --parallelism=1 \
            --command="python" \
            --args="manage.py,migrate" \
            --set-env-vars="ENVIRONMENT=$ENVIRONMENT" \
            --quiet

        # Execute migration job
        gcloud run jobs execute "$MIGRATION_JOB_NAME" \
            --region="$REGION" \
            --wait \
            --quiet

        # Clean up migration job
        gcloud run jobs delete "$MIGRATION_JOB_NAME" \
            --region="$REGION" \
            --quiet
    else
        log_info "[DRY RUN] Would run database migrations using temporary job"
    fi

    log_success "Database migrations completed"
}

# Collect static files
collect_static() {
    log_info "Collecting static files..."

    # Create a temporary Cloud Run job for static file collection
    STATIC_JOB_NAME="saleor-collectstatic-$(date +%s)"

    if [[ "$DRY_RUN" == false ]]; then
        # Create static collection job
        gcloud run jobs create "$STATIC_JOB_NAME" \
            --image="$REGION-docker.pkg.dev/$PROJECT_ID/saleor/saleor:$IMAGE_TAG" \
            --region="$REGION" \
            --memory=1Gi \
            --cpu=1 \
            --task-count=1 \
            --parallelism=1 \
            --command="python" \
            --args="manage.py,collectstatic,--no-input" \
            --set-env-vars="ENVIRONMENT=$ENVIRONMENT" \
            --quiet

        # Execute static collection job
        gcloud run jobs execute "$STATIC_JOB_NAME" \
            --region="$REGION" \
            --wait \
            --quiet

        # Clean up static collection job
        gcloud run jobs delete "$STATIC_JOB_NAME" \
            --region="$REGION" \
            --quiet
    else
        log_info "[DRY RUN] Would collect static files using temporary job"
    fi

    log_success "Static files collection completed"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    # Get Cloud Run service URL
    if [[ "$DRY_RUN" == false ]]; then
        SERVICE_URL=$(gcloud run services describe saleor-app \
            --region="$REGION" \
            --format="value(status.url)")

        if [[ -n "$SERVICE_URL" ]]; then
            log_info "Service URL: $SERVICE_URL"
            
            # Test health endpoint
            if curl -f "$SERVICE_URL/health/" > /dev/null 2>&1; then
                log_success "Health check passed"
            else
                log_warning "Health check failed - service may still be starting"
            fi
        else
            log_error "Could not get service URL"
        fi
    else
        log_info "[DRY RUN] Would verify deployment health"
    fi

    log_success "Deployment verification completed"
}

# Main deployment function
main() {
    log_info "Starting Saleor Google Cloud deployment..."
    log_info "Project ID: $PROJECT_ID"
    log_info "Region: $REGION"
    log_info "Environment: $ENVIRONMENT"
    log_info "Image Tag: $IMAGE_TAG"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_warning "DRY RUN MODE - No changes will be made"
    fi

    # Step 1: Check prerequisites
    check_prerequisites

    # Step 2: Deploy infrastructure
    deploy_infrastructure

    # Step 3: Build and push Docker images
    build_and_push_images

    # Step 4: Deploy to Cloud Run
    deploy_cloud_run

    # Step 5: Run database migrations
    run_migrations

    # Step 6: Collect static files
    collect_static

    # Step 7: Verify deployment
    verify_deployment

    log_success "Saleor deployment completed successfully!"
    log_info "Don't forget to:"
    log_info "1. Configure your domain DNS to point to the load balancer IP"
    log_info "2. Set up monitoring and alerting"
    log_info "3. Configure backup policies"
    log_info "4. Review security settings"
}

# Parse arguments and run main function
parse_args "$@"
main