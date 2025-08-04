#!/bin/bash

# Environment Setup Script for Betslip Converter
# This script helps set up the development and production environments

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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

# Function to check system requirements
check_system_requirements() {
    log_info "Checking system requirements..."
    
    # Check Node.js
    if command -v node &> /dev/null; then
        local node_version=$(node --version | sed 's/v//')
        local required_version="18.0.0"
        if [ "$(printf '%s\n' "$required_version" "$node_version" | sort -V | head -n1)" = "$required_version" ]; then
            log_success "Node.js $node_version is installed (>= $required_version required)"
        else
            log_error "Node.js $node_version is too old. Please install Node.js >= $required_version"
            exit 1
        fi
    else
        log_error "Node.js is not installed. Please install Node.js >= 18.0.0"
        exit 1
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version | cut -d' ' -f2)
        local required_python="3.11.0"
        if [ "$(printf '%s\n' "$required_python" "$python_version" | sort -V | head -n1)" = "$required_python" ]; then
            log_success "Python $python_version is installed (>= $required_python required)"
        else
            log_error "Python $python_version is too old. Please install Python >= $required_python"
            exit 1
        fi
    else
        log_error "Python 3 is not installed. Please install Python >= 3.11.0"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not installed. Please install pip3"
        exit 1
    fi
    
    log_success "System requirements check passed"
}

# Function to setup Python environment
setup_python_environment() {
    log_info "Setting up Python environment..."
    
    cd "$PROJECT_ROOT/automation"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Install Playwright browsers
    log_info "Installing Playwright browsers..."
    playwright install chromium
    playwright install-deps chromium
    
    log_success "Python environment setup completed"
}

# Function to setup Node.js environments
setup_nodejs_environments() {
    log_info "Setting up Node.js environments..."
    
    # Setup server dependencies
    log_info "Installing server dependencies..."
    cd "$PROJECT_ROOT/server"
    npm install
    
    # Setup client dependencies
    log_info "Installing client dependencies..."
    cd "$PROJECT_ROOT/client"
    npm install
    
    log_success "Node.js environments setup completed"
}

# Function to setup environment files
setup_environment_files() {
    log_info "Setting up environment files..."
    
    cd "$PROJECT_ROOT"
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        log_info "Creating .env file from template..."
        cp .env.template .env
        log_warning "Please edit .env file with your actual API keys and configuration"
    else
        log_info ".env file already exists"
    fi
    
    # Create production environment file if it doesn't exist
    if [ ! -f ".env.production" ]; then
        log_info ".env.production file already exists"
    else
        log_info ".env.production file already exists"
    fi
    
    log_success "Environment files setup completed"
}

# Function to setup MongoDB (local development)
setup_mongodb_local() {
    log_info "Setting up local MongoDB..."
    
    # Check if MongoDB is installed
    if command -v mongod &> /dev/null; then
        log_success "MongoDB is already installed"
    else
        log_warning "MongoDB is not installed locally"
        log_info "For local development, you can:"
        log_info "1. Install MongoDB locally: https://docs.mongodb.com/manual/installation/"
        log_info "2. Use Docker: docker run -d -p 27017:27017 --name mongodb mongo:7.0"
        log_info "3. Use MongoDB Atlas (cloud): https://www.mongodb.com/atlas"
    fi
    
    # Initialize MongoDB with sample data
    if command -v mongod &> /dev/null && pgrep mongod > /dev/null; then
        log_info "Initializing MongoDB with sample data..."
        cd "$PROJECT_ROOT"
        node server/cache-init.js
        log_success "MongoDB initialization completed"
    else
        log_warning "MongoDB is not running. Skipping initialization."
    fi
}

# Function to run tests
run_tests() {
    log_info "Running tests to verify setup..."
    
    # Test Python environment
    log_info "Testing Python environment..."
    cd "$PROJECT_ROOT/automation"
    source venv/bin/activate
    python -c "import browser_use; import playwright; print('Python environment OK')"
    
    # Test Node.js server
    log_info "Testing Node.js server..."
    cd "$PROJECT_ROOT/server"
    npm test
    
    # Test Node.js client
    log_info "Testing Node.js client..."
    cd "$PROJECT_ROOT/client"
    npm test
    
    log_success "All tests passed"
}

# Function to generate SSL certificates for development
generate_dev_ssl() {
    log_info "Generating development SSL certificates..."
    
    mkdir -p "$PROJECT_ROOT/deployment/ssl"
    cd "$PROJECT_ROOT/deployment/ssl"
    
    if [ ! -f "cert.pem" ] || [ ! -f "key.pem" ]; then
        # Generate self-signed certificate for development
        openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        log_success "Development SSL certificates generated"
        log_warning "These are self-signed certificates for development only"
    else
        log_info "SSL certificates already exist"
    fi
}

# Function to show setup summary
show_setup_summary() {
    log_info "Setup Summary:"
    echo
    echo "✅ System requirements checked"
    echo "✅ Python environment configured"
    echo "✅ Node.js environments configured"
    echo "✅ Environment files created"
    echo "✅ MongoDB setup guidance provided"
    echo "✅ Development SSL certificates generated"
    echo
    log_info "Next Steps:"
    echo "1. Edit .env file with your API keys:"
    echo "   - OPENAI_API_KEY: Get from https://platform.openai.com/api-keys"
    echo "   - MONGODB_URI: Configure your MongoDB connection"
    echo "   - JWT_SECRET: Generate a secure random string"
    echo
    echo "2. Start the development environment:"
    echo "   - MongoDB: Start your MongoDB instance"
    echo "   - Server: cd server && npm run dev"
    echo "   - Client: cd client && npm run dev"
    echo
    echo "3. For production deployment:"
    echo "   - Update .env.production with production values"
    echo "   - Run: ./scripts/deploy.sh production"
    echo
    log_success "Environment setup completed!"
}

# Main setup function
setup_environment() {
    log_info "Starting environment setup..."
    
    cd "$PROJECT_ROOT"
    
    check_system_requirements
    setup_python_environment
    setup_nodejs_environments
    setup_environment_files
    setup_mongodb_local
    generate_dev_ssl
    
    # Run tests if requested
    if [ "${1:-}" = "--with-tests" ]; then
        run_tests
    fi
    
    show_setup_summary
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  --with-tests    Run tests after setup"
    echo "  -h, --help      Show this help message"
    echo
    echo "This script will:"
    echo "  - Check system requirements (Node.js, Python)"
    echo "  - Set up Python virtual environment and dependencies"
    echo "  - Install Node.js dependencies for client and server"
    echo "  - Create environment configuration files"
    echo "  - Set up local MongoDB (if available)"
    echo "  - Generate development SSL certificates"
}

# Main script execution
case "${1:-}" in
    -h|--help)
        show_usage
        exit 0
        ;;
    --with-tests)
        setup_environment --with-tests
        ;;
    "")
        setup_environment
        ;;
    *)
        log_error "Invalid option: $1"
        show_usage
        exit 1
        ;;
esac