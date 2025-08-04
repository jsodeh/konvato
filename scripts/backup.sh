#!/bin/bash

# Backup script for betslip converter application
# Creates backups of MongoDB data and application configurations

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Create backup directory
create_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    log_info "Backup directory: $BACKUP_DIR"
}

# Backup MongoDB data
backup_mongodb() {
    log_info "Starting MongoDB backup..."
    
    local backup_path="$BACKUP_DIR/mongodb_$TIMESTAMP"
    mkdir -p "$backup_path"
    
    # Check if MongoDB is running in Docker
    if docker ps | grep -q betslip-mongodb; then
        log_info "Backing up MongoDB from Docker container..."
        docker exec betslip-mongodb mongodump \
            --username="${MONGO_ROOT_USERNAME:-admin}" \
            --password="${MONGO_ROOT_PASSWORD:-password}" \
            --authenticationDatabase=admin \
            --db=betslip_converter \
            --out=/tmp/backup
        
        docker cp betslip-mongodb:/tmp/backup "$backup_path/"
        docker exec betslip-mongodb rm -rf /tmp/backup
    else
        # Local MongoDB backup
        log_info "Backing up local MongoDB..."
        mongodump --db=betslip_converter --out="$backup_path"
    fi
    
    # Compress the backup
    tar -czf "$backup_path.tar.gz" -C "$BACKUP_DIR" "mongodb_$TIMESTAMP"
    rm -rf "$backup_path"
    
    log_success "MongoDB backup completed: mongodb_$TIMESTAMP.tar.gz"
}

# Backup Redis data
backup_redis() {
    log_info "Starting Redis backup..."
    
    local backup_path="$BACKUP_DIR/redis_$TIMESTAMP"
    mkdir -p "$backup_path"
    
    # Check if Redis is running in Docker
    if docker ps | grep -q betslip-redis; then
        log_info "Backing up Redis from Docker container..."
        docker exec betslip-redis redis-cli BGSAVE
        sleep 5  # Wait for background save to complete
        docker cp betslip-redis:/data/dump.rdb "$backup_path/"
    else
        # Local Redis backup
        log_info "Backing up local Redis..."
        redis-cli BGSAVE
        sleep 5
        cp /var/lib/redis/dump.rdb "$backup_path/" 2>/dev/null || \
        cp /usr/local/var/db/redis/dump.rdb "$backup_path/" 2>/dev/null || \
        log_warning "Could not find Redis dump file"
    fi
    
    # Compress the backup if dump file exists
    if [ -f "$backup_path/dump.rdb" ]; then
        tar -czf "$backup_path.tar.gz" -C "$BACKUP_DIR" "redis_$TIMESTAMP"
        rm -rf "$backup_path"
        log_success "Redis backup completed: redis_$TIMESTAMP.tar.gz"
    else
        rm -rf "$backup_path"
        log_warning "Redis backup skipped - no dump file found"
    fi
}

# Backup application configurations
backup_configs() {
    log_info "Starting configuration backup..."
    
    local backup_path="$BACKUP_DIR/configs_$TIMESTAMP"
    mkdir -p "$backup_path"
    
    # Copy configuration files
    cp "$PROJECT_ROOT/.env" "$backup_path/" 2>/dev/null || log_warning ".env file not found"
    cp "$PROJECT_ROOT/.env.production" "$backup_path/" 2>/dev/null || log_warning ".env.production file not found"
    cp -r "$PROJECT_ROOT/deployment" "$backup_path/" 2>/dev/null || log_warning "deployment directory not found"
    cp -r "$PROJECT_ROOT/monitoring" "$backup_path/" 2>/dev/null || log_warning "monitoring directory not found"
    
    # Compress the backup
    tar -czf "$backup_path.tar.gz" -C "$BACKUP_DIR" "configs_$TIMESTAMP"
    rm -rf "$backup_path"
    
    log_success "Configuration backup completed: configs_$TIMESTAMP.tar.gz"
}

# Backup application logs
backup_logs() {
    log_info "Starting logs backup..."
    
    local backup_path="$BACKUP_DIR/logs_$TIMESTAMP"
    mkdir -p "$backup_path"
    
    # Copy log files
    if [ -d "$PROJECT_ROOT/logs" ]; then
        cp -r "$PROJECT_ROOT/logs" "$backup_path/"
    fi
    
    # Copy Docker logs if available
    if docker ps | grep -q betslip-app; then
        docker logs betslip-app > "$backup_path/app.log" 2>&1
        docker logs betslip-mongodb > "$backup_path/mongodb.log" 2>&1
        docker logs betslip-redis > "$backup_path/redis.log" 2>&1
        docker logs betslip-nginx > "$backup_path/nginx.log" 2>&1
    fi
    
    # Compress the backup if logs exist
    if [ "$(ls -A $backup_path)" ]; then
        tar -czf "$backup_path.tar.gz" -C "$BACKUP_DIR" "logs_$TIMESTAMP"
        rm -rf "$backup_path"
        log_success "Logs backup completed: logs_$TIMESTAMP.tar.gz"
    else
        rm -rf "$backup_path"
        log_warning "No logs found to backup"
    fi
}

# Clean old backups
cleanup_old_backups() {
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."
    
    find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
    
    log_success "Old backups cleaned up"
}

# Create backup manifest
create_manifest() {
    local manifest_file="$BACKUP_DIR/backup_manifest_$TIMESTAMP.txt"
    
    cat > "$manifest_file" << EOF
Betslip Converter Backup Manifest
Generated: $(date)
Timestamp: $TIMESTAMP

Backup Files:
$(ls -la "$BACKUP_DIR"/*_$TIMESTAMP.tar.gz 2>/dev/null || echo "No backup files found")

System Information:
- Hostname: $(hostname)
- OS: $(uname -a)
- Docker Version: $(docker --version 2>/dev/null || echo "Not available")
- Disk Usage: $(df -h "$BACKUP_DIR")

Application Status:
$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep betslip || echo "No Docker containers running")
EOF

    log_success "Backup manifest created: backup_manifest_$TIMESTAMP.txt"
}

# Main backup function
run_backup() {
    log_info "Starting backup process..."
    
    create_backup_dir
    backup_mongodb
    backup_redis
    backup_configs
    backup_logs
    create_manifest
    cleanup_old_backups
    
    log_success "Backup process completed successfully!"
    log_info "Backup location: $BACKUP_DIR"
    log_info "Backup files:"
    ls -la "$BACKUP_DIR"/*_$TIMESTAMP.* 2>/dev/null || echo "No backup files found"
}

# Function to restore from backup
restore_backup() {
    local backup_timestamp="$1"
    
    if [ -z "$backup_timestamp" ]; then
        log_error "Please provide backup timestamp (format: YYYYMMDD_HHMMSS)"
        log_info "Available backups:"
        ls -la "$BACKUP_DIR"/*.tar.gz 2>/dev/null | grep -o '[0-9]\{8\}_[0-9]\{6\}' | sort -u || echo "No backups found"
        exit 1
    fi
    
    log_warning "This will restore data from backup $backup_timestamp"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Restore cancelled"
        exit 0
    fi
    
    log_info "Starting restore process..."
    
    # Stop services
    log_info "Stopping services..."
    docker-compose down
    
    # Restore MongoDB
    if [ -f "$BACKUP_DIR/mongodb_$backup_timestamp.tar.gz" ]; then
        log_info "Restoring MongoDB..."
        tar -xzf "$BACKUP_DIR/mongodb_$backup_timestamp.tar.gz" -C "$BACKUP_DIR"
        # Start MongoDB temporarily for restore
        docker-compose up -d mongodb
        sleep 10
        docker exec -i betslip-mongodb mongorestore \
            --username="${MONGO_ROOT_USERNAME:-admin}" \
            --password="${MONGO_ROOT_PASSWORD:-password}" \
            --authenticationDatabase=admin \
            --drop \
            /tmp/restore/betslip_converter
        rm -rf "$BACKUP_DIR/mongodb_$backup_timestamp"
    fi
    
    # Restore Redis
    if [ -f "$BACKUP_DIR/redis_$backup_timestamp.tar.gz" ]; then
        log_info "Restoring Redis..."
        tar -xzf "$BACKUP_DIR/redis_$backup_timestamp.tar.gz" -C "$BACKUP_DIR"
        docker-compose up -d redis
        sleep 5
        docker cp "$BACKUP_DIR/redis_$backup_timestamp/dump.rdb" betslip-redis:/data/
        docker restart betslip-redis
        rm -rf "$BACKUP_DIR/redis_$backup_timestamp"
    fi
    
    # Start all services
    log_info "Starting all services..."
    docker-compose up -d
    
    log_success "Restore completed successfully!"
}

# Show usage
show_usage() {
    echo "Usage: $0 [command] [options]"
    echo
    echo "Commands:"
    echo "  backup                 Create a full backup (default)"
    echo "  restore <timestamp>    Restore from backup"
    echo "  list                   List available backups"
    echo "  cleanup               Clean old backups"
    echo
    echo "Environment Variables:"
    echo "  BACKUP_DIR            Backup directory (default: ./backups)"
    echo "  RETENTION_DAYS        Days to keep backups (default: 7)"
    echo
    echo "Examples:"
    echo "  $0                           # Create backup"
    echo "  $0 restore 20231201_143000   # Restore from specific backup"
    echo "  $0 list                      # List available backups"
}

# List available backups
list_backups() {
    log_info "Available backups in $BACKUP_DIR:"
    echo
    
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A $BACKUP_DIR/*.tar.gz 2>/dev/null)" ]; then
        ls -la "$BACKUP_DIR"/*.tar.gz | while read -r line; do
            echo "$line"
        done
        echo
        
        log_info "Unique backup timestamps:"
        ls "$BACKUP_DIR"/*.tar.gz 2>/dev/null | grep -o '[0-9]\{8\}_[0-9]\{6\}' | sort -u
    else
        log_warning "No backups found"
    fi
}

# Main script execution
case "${1:-backup}" in
    backup)
        run_backup
        ;;
    restore)
        restore_backup "$2"
        ;;
    list)
        list_backups
        ;;
    cleanup)
        create_backup_dir
        cleanup_old_backups
        ;;
    -h|--help)
        show_usage
        ;;
    *)
        log_error "Invalid command: $1"
        show_usage
        exit 1
        ;;
esac