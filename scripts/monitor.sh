#!/bin/bash

# Monitoring and maintenance script for betslip converter
# Provides health checks, log analysis, and system maintenance

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Health check function
health_check() {
    log_info "Running comprehensive health check..."
    
    local overall_status="healthy"
    
    # Check Docker containers
    log_info "Checking Docker containers..."
    if ! docker ps --format "table {{.Names}}\t{{.Status}}" | grep betslip; then
        log_error "No betslip containers running"
        overall_status="unhealthy"
    else
        log_success "Docker containers are running"
    fi
    
    # Check API health
    log_info "Checking API health..."
    if curl -f -s http://localhost/api/health > /dev/null; then
        log_success "API is responding"
    else
        log_error "API health check failed"
        overall_status="unhealthy"
    fi
    
    # Check MongoDB
    log_info "Checking MongoDB..."
    if docker exec betslip-mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        log_success "MongoDB is responding"
    else
        log_error "MongoDB health check failed"
        overall_status="degraded"
    fi
    
    # Check Redis
    log_info "Checking Redis..."
    if docker exec betslip-redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis is responding"
    else
        log_error "Redis health check failed"
        overall_status="degraded"
    fi
    
    # Check disk space
    log_info "Checking disk space..."
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        log_error "Disk usage is ${disk_usage}% (critical)"
        overall_status="critical"
    elif [ "$disk_usage" -gt 80 ]; then
        log_warning "Disk usage is ${disk_usage}% (warning)"
        if [ "$overall_status" = "healthy" ]; then
            overall_status="degraded"
        fi
    else
        log_success "Disk usage is ${disk_usage}% (healthy)"
    fi
    
    # Check memory usage
    log_info "Checking memory usage..."
    local mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$mem_usage" -gt 90 ]; then
        log_error "Memory usage is ${mem_usage}% (critical)"
        overall_status="critical"
    elif [ "$mem_usage" -gt 80 ]; then
        log_warning "Memory usage is ${mem_usage}% (warning)"
        if [ "$overall_status" = "healthy" ]; then
            overall_status="degraded"
        fi
    else
        log_success "Memory usage is ${mem_usage}% (healthy)"
    fi
    
    log_info "Overall system status: $overall_status"
    
    case "$overall_status" in
        "healthy")
            exit 0
            ;;
        "degraded")
            exit 1
            ;;
        "unhealthy"|"critical")
            exit 2
            ;;
    esac
}

# Log analysis function
analyze_logs() {
    log_info "Analyzing application logs..."
    
    local log_dir="$PROJECT_ROOT/logs"
    local time_range="${1:-1h}"
    
    if [ ! -d "$log_dir" ]; then
        log_warning "Log directory not found: $log_dir"
        return
    fi
    
    # Error analysis
    log_info "Recent errors (last $time_range):"
    find "$log_dir" -name "*.log" -newermt "-$time_range" -exec grep -i "error\|exception\|failed" {} + | tail -20
    
    # Conversion statistics
    log_info "Conversion statistics (last $time_range):"
    find "$log_dir" -name "*.log" -newermt "-$time_range" -exec grep -c "Conversion completed successfully" {} + | \
        awk '{sum+=$1} END {print "Successful conversions: " sum}'
    
    find "$log_dir" -name "*.log" -newermt "-$time_range" -exec grep -c "Conversion failed" {} + | \
        awk '{sum+=$1} END {print "Failed conversions: " sum}'
    
    # Performance metrics
    log_info "Performance metrics (last $time_range):"
    find "$log_dir" -name "*.log" -newermt "-$time_range" -exec grep "processing time" {} + | \
        awk '{print $NF}' | sed 's/ms//' | \
        awk '{sum+=$1; count++} END {if(count>0) print "Average processing time: " sum/count "ms"}'
}

# System cleanup function
cleanup_system() {
    log_info "Running system cleanup..."
    
    # Clean Docker system
    log_info "Cleaning Docker system..."
    docker system prune -f
    
    # Clean old logs
    log_info "Cleaning old logs..."
    find "$PROJECT_ROOT/logs" -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    # Clean temporary files
    log_info "Cleaning temporary files..."
    find /tmp -name "betslip_*" -mtime +1 -delete 2>/dev/null || true
    
    # Restart services if needed
    if [ "${1:-}" = "--restart" ]; then
        log_info "Restarting services..."
        docker-compose restart
    fi
    
    log_success "System cleanup completed"
}

# Performance monitoring
monitor_performance() {
    log_info "Monitoring system performance..."
    
    local duration="${1:-60}"
    local interval="${2:-5}"
    
    log_info "Monitoring for ${duration} seconds (${interval}s intervals)..."
    
    for ((i=0; i<duration; i+=interval)); do
        echo "--- $(date) ---"
        
        # CPU usage
        echo "CPU Usage:"
        top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//'
        
        # Memory usage
        echo "Memory Usage:"
        free -h | awk 'NR==2{printf "Used: %s/%s (%.2f%%)\n", $3,$2,$3*100/$2}'
        
        # Docker stats
        echo "Container Stats:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
        
        # API response time
        echo "API Response Time:"
        curl -w "Response time: %{time_total}s\n" -o /dev/null -s http://localhost/api/health
        
        echo
        sleep "$interval"
    done
}

# Alert testing
test_alerts() {
    log_info "Testing alert system..."
    
    # Test webhook endpoint
    if command -v curl &> /dev/null; then
        log_info "Testing webhook endpoint..."
        curl -X POST http://localhost:5001/webhook \
            -H "Content-Type: application/json" \
            -d '{"alerts":[{"status":"firing","labels":{"alertname":"TestAlert","severity":"warning"},"annotations":{"summary":"Test alert from monitoring script"}}]}' \
            2>/dev/null && log_success "Webhook test successful" || log_warning "Webhook test failed"
    fi
    
    # Test email alerts (if configured)
    if [ -n "${ALERT_EMAIL:-}" ]; then
        log_info "Testing email alerts..."
        echo "Test alert from betslip converter monitoring" | \
            mail -s "Test Alert" "$ALERT_EMAIL" && \
            log_success "Email test successful" || log_warning "Email test failed"
    fi
}

# Generate monitoring report
generate_report() {
    local report_file="$PROJECT_ROOT/logs/monitoring_report_$(date +%Y%m%d_%H%M%S).txt"
    
    log_info "Generating monitoring report..."
    
    {
        echo "Betslip Converter Monitoring Report"
        echo "Generated: $(date)"
        echo "========================================"
        echo
        
        echo "System Information:"
        echo "- Hostname: $(hostname)"
        echo "- OS: $(uname -a)"
        echo "- Uptime: $(uptime)"
        echo
        
        echo "Docker Containers:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo
        
        echo "Resource Usage:"
        echo "CPU:"
        top -bn1 | grep "Cpu(s)"
        echo "Memory:"
        free -h
        echo "Disk:"
        df -h
        echo
        
        echo "Recent Logs (last 100 lines):"
        tail -100 "$PROJECT_ROOT/logs"/*.log 2>/dev/null || echo "No logs found"
        
    } > "$report_file"
    
    log_success "Monitoring report generated: $report_file"
}

# Show usage
show_usage() {
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  health                    Run health check"
    echo "  logs [time_range]         Analyze logs (default: 1h)"
    echo "  cleanup [--restart]       Clean system (optionally restart services)"
    echo "  monitor [duration] [interval]  Monitor performance (default: 60s, 5s)"
    echo "  alerts                    Test alert system"
    echo "  report                    Generate monitoring report"
    echo "  status                    Show system status"
    echo
    echo "Examples:"
    echo "  $0 health                 # Run health check"
    echo "  $0 logs 2h               # Analyze logs from last 2 hours"
    echo "  $0 cleanup --restart     # Clean system and restart services"
    echo "  $0 monitor 120 10        # Monitor for 2 minutes, 10s intervals"
}

# Show system status
show_status() {
    log_info "System Status Overview"
    echo
    
    echo "Docker Containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep betslip || echo "No betslip containers running"
    echo
    
    echo "API Health:"
    curl -s http://localhost/api/health | jq '.' 2>/dev/null || echo "API not responding"
    echo
    
    echo "Resource Usage:"
    echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')%"
    echo "Memory: $(free | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
    echo "Disk: $(df / | awk 'NR==2 {print $5}')"
    echo
    
    echo "Recent Activity:"
    tail -5 "$PROJECT_ROOT/logs"/*.log 2>/dev/null | grep -E "(ERROR|SUCCESS|WARNING)" | tail -10 || echo "No recent activity"
}

# Main execution
case "${1:-}" in
    health)
        health_check
        ;;
    logs)
        analyze_logs "${2:-1h}"
        ;;
    cleanup)
        cleanup_system "$2"
        ;;
    monitor)
        monitor_performance "${2:-60}" "${3:-5}"
        ;;
    alerts)
        test_alerts
        ;;
    report)
        generate_report
        ;;
    status)
        show_status
        ;;
    -h|--help)
        show_usage
        ;;
    *)
        log_error "Invalid command: ${1:-}"
        show_usage
        exit 1
        ;;
esac