#!/bin/bash

# BOQMate Deployment Script
# This script deploys the BOQMate application with security checks

set -e

echo "🚀 Starting BOQMate Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are installed"
}

# Check environment variables
check_environment() {
    print_status "Checking environment variables..."
    
    required_vars=(
        "JWT_SECRET_KEY"
        "ENCRYPTION_KEY"
        "OPENAI_API_KEY"
        "SUPABASE_JWT_SECRET"
        "SUPABASE_PROJECT_ID"
    )
    
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        print_error "Please set these variables in your .env file"
        exit 1
    fi
    
    print_status "All required environment variables are set"
}

# Check for default values
check_default_values() {
    print_status "Checking for default security values..."
    
    if [[ "$JWT_SECRET_KEY" == "your-super-secret-jwt-key-change-this" ]]; then
        print_warning "JWT_SECRET_KEY is using default value - CHANGE THIS!"
    fi
    
    if [[ "$ENCRYPTION_KEY" == "your-32-byte-encryption-key-here" ]]; then
        print_warning "ENCRYPTION_KEY is using default value - CHANGE THIS!"
    fi
    
    print_status "Security value check completed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p backend/uploads
    mkdir -p backend/logs
    mkdir -p ssl
    
    print_status "Directories created"
}

# Generate SSL certificates (self-signed for development)
generate_ssl() {
    if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
        print_status "Generating SSL certificates..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/key.pem \
            -out ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        print_status "SSL certificates generated"
    else
        print_status "SSL certificates already exist"
    fi
}

# Build and start services
deploy_services() {
    print_status "Building and starting services..."
    
    # Stop existing services
    docker-compose down
    
    # Build and start services
    docker-compose up --build -d
    
    print_status "Services deployed successfully"
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for backend
    timeout=60
    counter=0
    while ! curl -f http://localhost:8000/health &> /dev/null; do
        if [ $counter -ge $timeout ]; then
            print_error "Backend service failed to start within $timeout seconds"
            exit 1
        fi
        sleep 2
        counter=$((counter + 2))
    done
    
    print_status "Backend service is ready"
    
    # Wait for frontend
    timeout=60
    counter=0
    while ! curl -f http://localhost:3000 &> /dev/null; do
        if [ $counter -ge $timeout ]; then
            print_error "Frontend service failed to start within $timeout seconds"
            exit 1
        fi
        sleep 2
        counter=$((counter + 2))
    done
    
    print_status "Frontend service is ready"
}

# Run security checks
run_security_checks() {
    print_status "Running security checks..."
    
    # Check if security monitor is running
    if docker-compose ps | grep -q "backend.*Up"; then
        print_status "Security monitoring is active"
    else
        print_warning "Security monitoring may not be running"
    fi
    
    # Check SSL certificate
    if [ -f ssl/cert.pem ] && [ -f ssl/key.pem ]; then
        print_status "SSL certificates are in place"
    else
        print_warning "SSL certificates are missing"
    fi
}

# Display deployment information
show_deployment_info() {
    echo ""
    echo "🎉 BOQMate Deployment Complete!"
    echo "=================================="
    echo ""
    echo "🌐 Application URLs:"
    echo "  Frontend: https://localhost"
    echo "  Backend API: https://localhost/api"
    echo "  Health Check: https://localhost/health"
    echo ""
    echo "🔒 Security Features:"
    echo "  ✅ Rate limiting enabled"
    echo "  ✅ SSL/TLS encryption"
    echo "  ✅ Security headers"
    echo "  ✅ Input validation"
    echo "  ✅ File upload protection"
    echo "  ✅ Authentication middleware"
    echo ""
    echo "📊 Monitoring:"
    echo "  Security logs: backend/logs/"
    echo "  Docker logs: docker-compose logs"
    echo ""
    echo "🛠️  Management Commands:"
    echo "  Stop services: docker-compose down"
    echo "  View logs: docker-compose logs -f"
    echo "  Restart: docker-compose restart"
    echo ""
    echo "⚠️  Important Security Notes:"
    echo "  - Change default security keys in production"
    echo "  - Use proper SSL certificates in production"
    echo "  - Configure firewall rules"
    echo "  - Set up monitoring and alerting"
    echo ""
}

# Main deployment function
main() {
    print_status "Starting BOQMate deployment..."
    
    check_docker
    check_environment
    check_default_values
    create_directories
    generate_ssl
    deploy_services
    wait_for_services
    run_security_checks
    show_deployment_info
    
    print_status "Deployment completed successfully!"
}

# Run main function
main "$@"