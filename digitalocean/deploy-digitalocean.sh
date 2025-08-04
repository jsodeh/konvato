#!/bin/bash

# DigitalOcean Deployment Script for Betslip Converter
# This script deploys the application to DigitalOcean Kubernetes

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-production}"
REGION="${DO_REGION:-nyc1}"
CLUSTER_NAME="betslip-converter-${ENVIRONMENT}"

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
    
    # Check doctl
    if ! command -v doctl &> /dev/null; then
        log_error "doctl is not installed. Please install it first."
        log_info "Install with: brew install doctl (macOS) or download from GitHub"
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install it first."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check doctl authentication
    if ! doctl account get &> /dev/null; then
        log_error "doctl is not authenticated. Run 'doctl auth init' first."
        exit 1
    fi
    
    # Check required environment variables
    if [ -z "$DOMAIN_NAME" ]; then
        log_error "DOMAIN_NAME environment variable is required"
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
    
    if [ -z "$MONGODB_URI" ]; then
        log_error "MONGODB_URI environment variable is required"
        exit 1
    fi
    
    if [ -z "$REDIS_URL" ]; then
        log_error "REDIS_URL environment variable is required"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to create DigitalOcean resources
create_do_resources() {
    log_info "Creating DigitalOcean resources..."
    
    # Create Kubernetes cluster if it doesn't exist
    if ! doctl kubernetes cluster get "$CLUSTER_NAME" &> /dev/null; then
        log_info "Creating Kubernetes cluster..."
        doctl kubernetes cluster create "$CLUSTER_NAME" \
            --region "$REGION" \
            --version "1.28.2-do.0" \
            --count 3 \
            --size "s-2vcpu-4gb" \
            --auto-upgrade=true \
            --maintenance-window="saturday=06:00" \
            --surge-upgrade=true \
            --ha=true \
            --wait
        log_success "Kubernetes cluster created"
    else
        log_info "Kubernetes cluster already exists"
    fi
    
    # Create container registry if it doesn't exist
    local registry_name="betslip-converter"
    if ! doctl registry get "$registry_name" &> /dev/null; then
        log_info "Creating container registry..."
        doctl registry create "$registry_name" --subscription-tier basic
        log_success "Container registry created"
    else
        log_info "Container registry already exists"
    fi
    
    # Create managed MongoDB database
    local mongodb_name="betslip-mongodb-${ENVIRONMENT}"
    if ! doctl databases get "$mongodb_name" &> /dev/null; then
        log_info "Creating managed MongoDB database..."
        doctl databases create "$mongodb_name" \
            --engine mongodb \
            --region "$REGION" \
            --size "db-s-2vcpu-2gb" \
            --num-nodes 1 \
            --version 5
        
        log_info "Waiting for MongoDB to be ready..."
        while [ "$(doctl databases get "$mongodb_name" --format Status --no-header)" != "online" ]; do
            sleep 30
            log_info "Still waiting for MongoDB..."
        done
        log_success "MongoDB database created"
    else
        log_info "MongoDB database already exists"
    fi
    
    # Create managed Redis database
    local redis_name="betslip-redis-${ENVIRONMENT}"
    if ! doctl databases get "$redis_name" &> /dev/null; then
        log_info "Creating managed Redis database..."
        doctl databases create "$redis_name" \
            --engine redis \
            --region "$REGION" \
            --size "db-s-1vcpu-1gb" \
            --num-nodes 1 \
            --version 7
        
        log_info "Waiting for Redis to be ready..."
        while [ "$(doctl databases get "$redis_name" --format Status --no-header)" != "online" ]; do
            sleep 30
            log_info "Still waiting for Redis..."
        done
        log_success "Redis database created"
    else
        log_info "Redis database already exists"
    fi
}

# Function to configure kubectl
configure_kubectl() {
    log_info "Configuring kubectl..."
    
    # Save kubeconfig
    doctl kubernetes cluster kubeconfig save "$CLUSTER_NAME"
    
    # Verify connection
    kubectl cluster-info
    
    log_success "kubectl configured successfully"
}

# Function to build and push Docker image
build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    cd "$PROJECT_ROOT"
    
    # Login to DigitalOcean Container Registry
    doctl registry login
    
    # Build image
    log_info "Building Docker image..."
    docker build -t betslip-converter:latest .
    
    # Tag image for registry
    local registry_url="registry.digitalocean.com/betslip-converter"
    docker tag betslip-converter:latest "$registry_url/betslip-converter:latest"
    docker tag betslip-converter:latest "$registry_url/betslip-converter:$ENVIRONMENT"
    
    # Push image
    log_info "Pushing Docker image to registry..."
    docker push "$registry_url/betslip-converter:latest"
    docker push "$registry_url/betslip-converter:$ENVIRONMENT"
    
    log_success "Docker image pushed successfully"
}

# Function to create Kubernetes secrets
create_k8s_secrets() {
    log_info "Creating Kubernetes secrets..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace betslip-converter --dry-run=client -o yaml | kubectl apply -f -
    
    # Encode secrets
    local openai_key_encoded=$(echo -n "$OPENAI_API_KEY" | base64)
    local jwt_secret_encoded=$(echo -n "$JWT_SECRET" | base64)
    local mongodb_uri_encoded=$(echo -n "$MONGODB_URI" | base64)
    local redis_url_encoded=$(echo -n "$REDIS_URL" | base64)
    
    # Create secrets manifest
    cat > /tmp/betslip-secrets.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: betslip-secrets
  namespace: betslip-converter
type: Opaque
data:
  openai-api-key: $openai_key_encoded
  jwt-secret: $jwt_secret_encoded
  mongodb-uri: $mongodb_uri_encoded
  redis-url: $redis_url_encoded
EOF
    
    # Apply secrets
    kubectl apply -f /tmp/betslip-secrets.yaml
    rm /tmp/betslip-secrets.yaml
    
    log_success "Kubernetes secrets created"
}

# Function to update deployment manifest
update_deployment_manifest() {
    log_info "Updating deployment manifest..."
    
    local manifest_file="$SCRIPT_DIR/k8s-deployment.yaml"
    local temp_manifest="/tmp/k8s-deployment-updated.yaml"
    
    # Replace placeholders in manifest
    sed "s|registry.digitalocean.com/your-registry|registry.digitalocean.com/betslip-converter|g" "$manifest_file" > "$temp_manifest"
    sed -i "s|your-domain.com|$DOMAIN_NAME|g" "$temp_manifest"
    
    # Update ConfigMap with environment-specific values
    if [ "$ENVIRONMENT" = "development" ]; then
        sed -i 's|"production"|"development"|g' "$temp_manifest"
        sed -i 's|replicas: 3|replicas: 1|g' "$temp_manifest"
        sed -i 's|minReplicas: 3|minReplicas: 1|g' "$temp_manifest"
        sed -i 's|maxReplicas: 10|maxReplicas: 3|g' "$temp_manifest"
    fi
    
    echo "$temp_manifest"
}

# Function to deploy to Kubernetes
deploy_to_kubernetes() {
    log_info "Deploying to Kubernetes..."
    
    local manifest_file=$(update_deployment_manifest)
    
    # Apply the deployment
    kubectl apply -f "$manifest_file"
    
    # Wait for deployment to be ready
    log_info "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=600s deployment/betslip-converter -n betslip-converter
    
    # Clean up temp file
    rm "$manifest_file"
    
    log_success "Kubernetes deployment completed"
}

# Function to setup ingress controller
setup_ingress_controller() {
    log_info "Setting up ingress controller..."
    
    # Check if ingress-nginx is already installed
    if ! kubectl get namespace ingress-nginx &> /dev/null; then
        log_info "Installing ingress-nginx controller..."
        kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/do/deploy.yaml
        
        # Wait for ingress controller to be ready
        kubectl wait --namespace ingress-nginx \
            --for=condition=ready pod \
            --selector=app.kubernetes.io/component=controller \
            --timeout=300s
        
        log_success "Ingress controller installed"
    else
        log_info "Ingress controller already exists"
    fi
}

# Function to setup cert-manager for SSL
setup_cert_manager() {
    log_info "Setting up cert-manager for SSL..."
    
    # Check if cert-manager is already installed
    if ! kubectl get namespace cert-manager &> /dev/null; then
        log_info "Installing cert-manager..."
        kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml
        
        # Wait for cert-manager to be ready
        kubectl wait --for=condition=available --timeout=300s deployment/cert-manager -n cert-manager
        kubectl wait --for=condition=available --timeout=300s deployment/cert-manager-cainjector -n cert-manager
        kubectl wait --for=condition=available --timeout=300s deployment/cert-manager-webhook -n cert-manager
        
        # Create ClusterIssuer for Let's Encrypt
        cat > /tmp/letsencrypt-issuer.yaml << EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@$DOMAIN_NAME
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
        
        kubectl apply -f /tmp/letsencrypt-issuer.yaml
        rm /tmp/letsencrypt-issuer.yaml
        
        log_success "cert-manager installed and configured"
    else
        log_info "cert-manager already exists"
    fi
}

# Function to setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Create monitoring namespace
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
    
    # Install Prometheus using Helm (if available) or kubectl
    if command -v helm &> /dev/null; then
        log_info "Installing Prometheus with Helm..."
        helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
        helm repo update
        
        helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
            --namespace monitoring \
            --set grafana.adminPassword=admin123 \
            --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
            --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false
    else
        log_warning "Helm not found, skipping Prometheus installation"
        log_info "You can install monitoring manually using the monitoring stack"
    fi
    
    log_success "Monitoring setup completed"
}

# Function to run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Get load balancer IP
    local max_attempts=30
    local attempt=1
    local lb_ip=""
    
    while [ $attempt -le $max_attempts ] && [ -z "$lb_ip" ]; do
        lb_ip=$(kubectl get service betslip-converter-service -n betslip-converter -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        
        if [ -z "$lb_ip" ]; then
            log_info "Waiting for load balancer IP (attempt $attempt/$max_attempts)..."
            sleep 30
            ((attempt++))
        fi
    done
    
    if [ -z "$lb_ip" ]; then
        log_error "Failed to get load balancer IP after $max_attempts attempts"
        return 1
    fi
    
    log_info "Load Balancer IP: $lb_ip"
    
    # Test health endpoint
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "http://$lb_ip/api/health" > /dev/null; then
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
    
    # Show pods
    echo "Pods:"
    kubectl get pods -n betslip-converter -o wide
    echo
    
    # Show services
    echo "Services:"
    kubectl get services -n betslip-converter
    echo
    
    # Show ingress
    echo "Ingress:"
    kubectl get ingress -n betslip-converter
    echo
    
    # Show HPA
    echo "Horizontal Pod Autoscaler:"
    kubectl get hpa -n betslip-converter
    echo
    
    # Get load balancer IP
    local lb_ip=$(kubectl get service betslip-converter-service -n betslip-converter -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending")
    
    log_info "Service URLs:"
    echo "  - Application: https://$DOMAIN_NAME"
    echo "  - Load Balancer IP: $lb_ip"
    echo "  - Health Check: http://$lb_ip/api/health"
    echo
    
    log_info "DigitalOcean Resources:"
    echo "  - Kubernetes Cluster: $CLUSTER_NAME"
    echo "  - Container Registry: registry.digitalocean.com/betslip-converter"
    echo "  - MongoDB: betslip-mongodb-${ENVIRONMENT}"
    echo "  - Redis: betslip-redis-${ENVIRONMENT}"
    echo
    
    log_info "Useful Commands:"
    echo "  - View logs: kubectl logs -f deployment/betslip-converter -n betslip-converter"
    echo "  - Scale app: kubectl scale deployment betslip-converter --replicas=5 -n betslip-converter"
    echo "  - Port forward: kubectl port-forward service/betslip-converter-service 8080:80 -n betslip-converter"
}

# Function to cleanup on failure
cleanup_on_failure() {
    log_warning "Deployment failed, cleaning up..."
    
    # Optionally delete the deployment
    if [ "${CLEANUP_ON_FAILURE:-false}" = "true" ]; then
        log_info "Cleaning up Kubernetes resources..."
        kubectl delete namespace betslip-converter --ignore-not-found=true
    fi
}

# Main deployment function
deploy_to_digitalocean() {
    log_info "Starting DigitalOcean deployment for environment: $ENVIRONMENT"
    
    # Set trap for cleanup on failure
    trap cleanup_on_failure ERR
    
    # Run deployment steps
    check_prerequisites
    create_do_resources
    configure_kubectl
    build_and_push_image
    create_k8s_secrets
    setup_ingress_controller
    setup_cert_manager
    deploy_to_kubernetes
    setup_monitoring
    
    # Run health checks
    if run_health_checks; then
        show_deployment_status
        log_success "DigitalOcean deployment completed successfully!"
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
    echo "  DOMAIN_NAME     Domain name for the application"
    echo "  OPENAI_API_KEY  OpenAI API key"
    echo "  JWT_SECRET      JWT secret for token signing"
    echo "  MONGODB_URI     MongoDB connection URI"
    echo "  REDIS_URL       Redis connection URL"
    echo
    echo "Optional Environment Variables:"
    echo "  DO_REGION           DigitalOcean region (default: nyc1)"
    echo "  CLEANUP_ON_FAILURE  Cleanup on failure (default: false)"
    echo
    echo "Examples:"
    echo "  DOMAIN_NAME=betslip.example.com MONGODB_URI=... $0"
    echo "  $0 staging"
}

# Main script execution
case "${1:-}" in
    -h|--help)
        show_usage
        exit 0
        ;;
    ""|production|staging|development)
        deploy_to_digitalocean
        ;;
    *)
        log_error "Invalid environment: $1"
        show_usage
        exit 1
        ;;
esac