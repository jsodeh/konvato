#!/bin/bash

# Betslip Converter Deployment Script
# This script handles the deployment of the betslip converter application

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-production}"
COMPOSE_FILE="docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to validate environment configuration
validate_environment() {
    log_info "Validating environment configuration..."
    
    local env_file=".env"
    if [ "$ENVIRONMENT" = "production" ]; then
        env_file=".env.production"
    fi
    
    if [ ! -f "$env_file" ]; then
        log_error "Environment file $env_file not found. Please create it from .env.template"
        exit 1
    fi
    
    # Check for required environment variables
    local required_vars=("OPENAI_API_KEY" "MONGODB_URI" "JWT_SECRET")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$env_file" || grep -q "^${var}=.*your_.*_here" "$env_file"; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "Missing or placeholder values for required environment variables:"
        for var in "${missing_vars[@]}"; do
            log_error "  - $var"
        done
        log_error "Please update $env_file with actual values"
        exit 1
    fi
    
    log_success "Environment configuration validated"
}

# Function to create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p logs/nginx
    mkdir -p deployment/ssl
    mkdir -p data/mongodb
    mkdir -p data/redis
    
    log_success "Directories created"
}

# Function to build Docker images
build_images() {
    log_info "Building Docker images..."
    
    # Build the main application image
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    log_success "Docker images built successfully"
}

# Function to start services
start_services() {
    log_info "Starting services..."
    
    # Start services in the correct order
    docker-compose -f "$COMPOSE_FILE" up -d mongodb redis
    
    # Wait for MongoDB to be ready
    log_info "Waiting for MongoDB to be ready..."
    sleep 10
    
    # Start the main application
    docker-compose -f "$COMPOSE_FILE" up -d app
    
    # Wait for app to be ready
    log_info "Waiting for application to be ready..."
    sleep 15
    
    # Start nginx
    docker-compose -f "$COMPOSE_FILE" up -d nginx
    
    log_success "All services started"
}

# Function to run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost/health > /dev/null; then
            log_success "Health check passed"
            return 0
        fi
        
        log_info "Health check attempt $attempt/$max_attempts failed, retrying in 10 seconds..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Health checks failed after $max_attempts attempts"
    return 1
}

# Function to show deployment status
show_status() {
    log_info "Deployment Status:"
    echo
    docker-compose -f "$COMPOSE_FILE" ps
    echo
    
    log_info "Service URLs:"
    echo "  - Application: http://localhost"
    echo "  - API Health: http://localhost/api/health"
    echo "  - MongoDB: localhost:27017"
    echo "  - Redis: localhost:6379"
    echo
    
    log_info "Logs:"
    echo "  - Application logs: docker-compose logs app"
    echo "  - MongoDB logs: docker-compose logs mongodb"
    echo "  - Nginx logs: docker-compose logs nginx"
}

# Function to cleanup on failure
cleanup_on_failure() {
    log_warning "Deployment failed, cleaning up..."
    docker-compose -f "$COMPOSE_FILE" down
    log_info "Cleanup completed"
}

# Main deployment function
deploy() {
    log_info "Starting deployment for environment: $ENVIRONMENT"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Set trap for cleanup on failure
    trap cleanup_on_failure ERR
    
    # Run deployment steps
    check_prerequisites
    validate_environment
    create_directories
    build_images
    start_services
    
    # Run health checks
    if run_health_checks; then
        show_status
        log_success "Deployment completed successfully!"
    else
        log_error "Deployment failed health checks"
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [environment]"
    echo
    echo "Arguments:"
    echo "  environment    Deployment environment (default: production)"
    echo
    echo "Examples:"
    echo "  $0                 # Deploy to production"
    echo "  $0 production      # Deploy to production"
    echo "  $0 development     # Deploy to development"
}

# Main script execution
case "${1:-}" in
    -h|--help)
        show_usage
        exit 0
        ;;
    ""|production|development)
        deploy
        ;;
    *)
        log_error "Invalid environment: $1"
        show_usage
        exit 1
        ;;
esac