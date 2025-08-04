#!/bin/bash

# AWS Deployment Script for Betslip Converter
# This script deploys the application to AWS using CloudFormation and ECS

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-production}"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
STACK_NAME="betslip-converter-${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    # Check required environment variables
    if [ -z "$DOMAIN_NAME" ]; then
        log_error "DOMAIN_NAME environment variable is required"
        exit 1
    fi
    
    if [ -z "$CERTIFICATE_ARN" ]; then
        log_error "CERTIFICATE_ARN environment variable is required"
        exit 1
    fi
    
    if [ -z "$OPENAI_API_KEY" ]; then
        log_error "OPENAI_API_KEY environment variable is required"
        exit 1
    fi
    
    if [ -z "$JWT_SECRET" ]; then
        log_error "JWT_SECRET environment variable is required"
        exit 1
    fi
    
    if [ -z "$DATABASE_PASSWORD" ]; then
        log_error "DATABASE_PASSWORD environment variable is required"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to create ECR repository
create_ecr_repository() {
    log_info "Creating ECR repository..."
    
    local repo_name="betslip-converter"
    
    # Check if repository exists
    if aws ecr describe-repositories --repository-names "$repo_name" --region "$REGION" &> /dev/null; then
        log_info "ECR repository already exists"
    else
        aws ecr create-repository \
            --repository-name "$repo_name" \
            --region "$REGION" \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256
        log_success "ECR repository created"
    fi
    
    # Get repository URI
    ECR_URI=$(aws ecr describe-repositories \
        --repository-names "$repo_name" \
        --region "$REGION" \
        --query 'repositories[0].repositoryUri' \
        --output text)
    
    log_info "ECR Repository URI: $ECR_URI"
}

# Function to build and push Docker image
build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    cd "$PROJECT_ROOT"
    
    # Get ECR login token
    aws ecr get-login-password --region "$REGION" | \
        docker login --username AWS --password-stdin "$ECR_URI"
    
    # Build image
    log_info "Building Docker image..."
    docker build -t betslip-converter:latest .
    
    # Tag image for ECR
    docker tag betslip-converter:latest "$ECR_URI:latest"
    docker tag betslip-converter:latest "$ECR_URI:$ENVIRONMENT"
    
    # Push image
    log_info "Pushing Docker image to ECR..."
    docker push "$ECR_URI:latest"
    docker push "$ECR_URI:$ENVIRONMENT"
    
    log_success "Docker image pushed successfully"
}

# Function to deploy CloudFormation stack
deploy_cloudformation() {
    log_info "Deploying CloudFormation stack..."
    
    local template_file="$SCRIPT_DIR/cloudformation-template.yaml"
    local parameters_file="$SCRIPT_DIR/parameters-${ENVIRONMENT}.json"
    
    # Create parameters file if it doesn't exist
    if [ ! -f "$parameters_file" ]; then
        log_info "Creating parameters file..."
        cat > "$parameters_file" << EOF
[
  {
    "ParameterKey": "Environment",
    "ParameterValue": "$ENVIRONMENT"
  },
  {
    "ParameterKey": "DomainName",
    "ParameterValue": "$DOMAIN_NAME"
  },
  {
    "ParameterKey": "CertificateArn",
    "ParameterValue": "$CERTIFICATE_ARN"
  },
  {
    "ParameterKey": "OpenAIApiKey",
    "ParameterValue": "$OPENAI_API_KEY"
  },
  {
    "ParameterKey": "JWTSecret",
    "ParameterValue": "$JWT_SECRET"
  },
  {
    "ParameterKey": "DatabasePassword",
    "ParameterValue": "$DATABASE_PASSWORD"
  }
]
EOF
    fi
    
    # Check if stack exists
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
        log_info "Updating existing CloudFormation stack..."
        aws cloudformation update-stack \
            --stack-name "$STACK_NAME" \
            --template-body "file://$template_file" \
            --parameters "file://$parameters_file" \
            --capabilities CAPABILITY_IAM \
            --region "$REGION"
        
        log_info "Waiting for stack update to complete..."
        aws cloudformation wait stack-update-complete \
            --stack-name "$STACK_NAME" \
            --region "$REGION"
    else
        log_info "Creating new CloudFormation stack..."
        aws cloudformation create-stack \
            --stack-name "$STACK_NAME" \
            --template-body "file://$template_file" \
            --parameters "file://$parameters_file" \
            --capabilities CAPABILITY_IAM \
            --region "$REGION" \
            --enable-termination-protection
        
        log_info "Waiting for stack creation to complete..."
        aws cloudformation wait stack-create-complete \
            --stack-name "$STACK_NAME" \
            --region "$REGION"
    fi
    
    log_success "CloudFormation stack deployed successfully"
}

# Function to update ECS service
update_ecs_service() {
    log_info "Updating ECS service..."
    
    local cluster_name="${ENVIRONMENT}-betslip-cluster"
    local service_name="${ENVIRONMENT}-betslip-converter-service"
    
    # Force new deployment
    aws ecs update-service \
        --cluster "$cluster_name" \
        --service "$service_name" \
        --force-new-deployment \
        --region "$REGION"
    
    log_info "Waiting for service to stabilize..."
    aws ecs wait services-stable \
        --cluster "$cluster_name" \
        --services "$service_name" \
        --region "$REGION"
    
    log_success "ECS service updated successfully"
}

# Function to create CloudWatch dashboard
create_cloudwatch_dashboard() {
    log_info "Creating CloudWatch dashboard..."
    
    local dashboard_name="BetslipConverter-${ENVIRONMENT}"
    local dashboard_body=$(cat << EOF
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/ECS", "CPUUtilization", "ServiceName", "${ENVIRONMENT}-betslip-converter-service", "ClusterName", "${ENVIRONMENT}-betslip-cluster" ],
          [ ".", "MemoryUtilization", ".", ".", ".", "." ]
        ],
        "period": 300,
        "stat": "Average",
        "region": "$REGION",
        "title": "ECS Service Metrics"
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/ApplicationELB", "RequestCount", "LoadBalancer", "${ENVIRONMENT}-betslip-alb" ],
          [ ".", "TargetResponseTime", ".", "." ],
          [ ".", "HTTPCode_Target_2XX_Count", ".", "." ],
          [ ".", "HTTPCode_Target_5XX_Count", ".", "." ]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "$REGION",
        "title": "Load Balancer Metrics"
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/DocDB", "CPUUtilization", "DBClusterIdentifier", "${ENVIRONMENT}-betslip-docdb" ],
          [ ".", "DatabaseConnections", ".", "." ]
        ],
        "period": 300,
        "stat": "Average",
        "region": "$REGION",
        "title": "DocumentDB Metrics"
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/ElastiCache", "CPUUtilization", "CacheClusterId", "${ENVIRONMENT}-betslip-redis" ],
          [ ".", "CurrConnections", ".", "." ]
        ],
        "period": 300,
        "stat": "Average",
        "region": "$REGION",
        "title": "ElastiCache Metrics"
      }
    }
  ]
}
EOF
)
    
    aws cloudwatch put-dashboard \
        --dashboard-name "$dashboard_name" \
        --dashboard-body "$dashboard_body" \
        --region "$REGION"
    
    log_success "CloudWatch dashboard created"
}

# Function to setup CloudWatch alarms
setup_cloudwatch_alarms() {
    log_info "Setting up CloudWatch alarms..."
    
    # High CPU alarm
    aws cloudwatch put-metric-alarm \
        --alarm-name "${ENVIRONMENT}-betslip-high-cpu" \
        --alarm-description "High CPU utilization" \
        --metric-name CPUUtilization \
        --namespace AWS/ECS \
        --statistic Average \
        --period 300 \
        --threshold 80 \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 2 \
        --alarm-actions "arn:aws:sns:${REGION}:$(aws sts get-caller-identity --query Account --output text):betslip-alerts" \
        --dimensions Name=ServiceName,Value="${ENVIRONMENT}-betslip-converter-service" Name=ClusterName,Value="${ENVIRONMENT}-betslip-cluster" \
        --region "$REGION"
    
    # High error rate alarm
    aws cloudwatch put-metric-alarm \
        --alarm-name "${ENVIRONMENT}-betslip-high-errors" \
        --alarm-description "High error rate" \
        --metric-name HTTPCode_Target_5XX_Count \
        --namespace AWS/ApplicationELB \
        --statistic Sum \
        --period 300 \
        --threshold 10 \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 2 \
        --treat-missing-data notBreaching \
        --alarm-actions "arn:aws:sns:${REGION}:$(aws sts get-caller-identity --query Account --output text):betslip-alerts" \
        --dimensions Name=LoadBalancer,Value="${ENVIRONMENT}-betslip-alb" \
        --region "$REGION"
    
    log_success "CloudWatch alarms configured"
}

# Function to run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Get load balancer DNS
    local alb_dns=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
        --output text)
    
    log_info "Load Balancer DNS: $alb_dns"
    
    # Wait for service to be available
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "https://$alb_dns/api/health" > /dev/null; then
            log_success "Health check passed"
            break
        fi
        
        log_info "Health check attempt $attempt/$max_attempts failed, retrying in 30 seconds..."
        sleep 30
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "Health checks failed after $max_attempts attempts"
        return 1
    fi
}

# Function to show deployment status
show_deployment_status() {
    log_info "Deployment Status:"
    echo
    
    # Stack outputs
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
        --output table
    
    echo
    log_info "Service URLs:"
    local alb_dns=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
        --output text)
    
    echo "  - Application: https://$DOMAIN_NAME"
    echo "  - Load Balancer: https://$alb_dns"
    echo "  - Health Check: https://$alb_dns/api/health"
    echo
    
    log_info "AWS Resources:"
    echo "  - CloudFormation Stack: $STACK_NAME"
    echo "  - ECS Cluster: ${ENVIRONMENT}-betslip-cluster"
    echo "  - ECR Repository: $ECR_URI"
    echo "  - CloudWatch Dashboard: BetslipConverter-${ENVIRONMENT}"
}

# Function to cleanup on failure
cleanup_on_failure() {
    log_warning "Deployment failed, cleaning up..."
    
    # Optionally rollback CloudFormation stack
    if [ "${ROLLBACK_ON_FAILURE:-true}" = "true" ]; then
        log_info "Rolling back CloudFormation stack..."
        aws cloudformation cancel-update-stack \
            --stack-name "$STACK_NAME" \
            --region "$REGION" 2>/dev/null || true
    fi
}

# Main deployment function
deploy_to_aws() {
    log_info "Starting AWS deployment for environment: $ENVIRONMENT"
    
    # Set trap for cleanup on failure
    trap cleanup_on_failure ERR
    
    # Run deployment steps
    check_prerequisites
    create_ecr_repository
    build_and_push_image
    deploy_cloudformation
    update_ecs_service
    create_cloudwatch_dashboard
    setup_cloudwatch_alarms
    
    # Run health checks
    if run_health_checks; then
        show_deployment_status
        log_success "AWS deployment completed successfully!"
    else
        log_error "Deployment failed health checks"
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [environment] [options]"
    echo
    echo "Arguments:"
    echo "  environment    Deployment environment (default: production)"
    echo
    echo "Required Environment Variables:"
    echo "  DOMAIN_NAME         Domain name for the application"
    echo "  CERTIFICATE_ARN     SSL certificate ARN from ACM"
    echo "  OPENAI_API_KEY      OpenAI API key"
    echo "  JWT_SECRET          JWT secret for token signing"
    echo "  DATABASE_PASSWORD   Database password"
    echo
    echo "Optional Environment Variables:"
    echo "  AWS_DEFAULT_REGION  AWS region (default: us-east-1)"
    echo "  ROLLBACK_ON_FAILURE Rollback on failure (default: true)"
    echo
    echo "Examples:"
    echo "  DOMAIN_NAME=betslip.example.com CERTIFICATE_ARN=arn:aws:acm:... $0"
    echo "  $0 staging"
}

# Main script execution
case "${1:-}" in
    -h|--help)
        show_usage
        exit 0
        ;;
    ""|production|staging|development)
        deploy_to_aws
        ;;
    *)
        log_error "Invalid environment: $1"
        show_usage
        exit 1
        ;;
esac