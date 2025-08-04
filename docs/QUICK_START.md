# Quick Start Guide

Get the Betslip Converter up and running in minutes with your preferred deployment method.

## 🚀 Choose Your Deployment

### Option 1: Docker (Recommended for beginners)
**Time:** 15 minutes | **Cost:** $0-50/month | **Difficulty:** Easy

```bash
# 1. Clone and setup
git clone <repository-url>
cd betslip-converter
./scripts/setup-environment.sh

# 2. Configure environment
cp .env.template .env
# Edit .env with your API keys (see configuration section below)

# 3. Deploy
./scripts/deploy.sh

# 4. Access application
open http://localhost
```

### Option 2: LocalStack (For AWS development)
**Time:** 30 minutes | **Cost:** $0 | **Difficulty:** Medium

```bash
# 1. Install LocalStack
pip install localstack awscli-local

# 2. Start LocalStack
localstack start -d

# 3. Deploy application
cp .env.template .env.localstack
# Edit .env.localstack with LocalStack settings
docker-compose -f docker-compose.localstack.yml up -d

# 4. Access application
open http://localhost
```

### Option 3: DigitalOcean (Production ready)
**Time:** 1-2 hours | **Cost:** $150-360/month | **Difficulty:** Medium

```bash
# 1. Setup DigitalOcean CLI
brew install doctl  # or download from GitHub
doctl auth init

# 2. Set environment variables
export DOMAIN_NAME="your-domain.com"
export OPENAI_API_KEY="your-openai-key"
export JWT_SECRET="your-jwt-secret"
export MONGODB_URI="your-mongodb-uri"
export REDIS_URL="your-redis-url"

# 3. Deploy
./digitalocean/deploy-digitalocean.sh

# 4. Access application
open https://your-domain.com
```

### Option 4: AWS (Enterprise scale)
**Time:** 2-4 hours | **Cost:** $230-720+/month | **Difficulty:** Hard

```bash
# 1. Configure AWS CLI
aws configure

# 2. Set environment variables
export DOMAIN_NAME="your-domain.com"
export CERTIFICATE_ARN="arn:aws:acm:..."
export OPENAI_API_KEY="your-openai-key"
export JWT_SECRET="your-jwt-secret"
export DATABASE_PASSWORD="your-db-password"

# 3. Deploy
./aws/deploy-aws.sh

# 4. Access application
open https://your-domain.com
```

## 🔧 Configuration

### Required API Keys

1. **OpenAI API Key** (Required)
   - Get from: https://platform.openai.com/api-keys
   - Used for: Browser automation intelligence
   - Cost: ~$0.01-0.10 per conversion

2. **JWT Secret** (Required)
   - Generate: `openssl rand -base64 32`
   - Used for: Session management
   - Keep secure and unique per environment

### Optional Services

3. **Odds API Key** (Optional)
   - Get from: https://the-odds-api.com/
   - Used for: Enhanced odds comparison
   - Cost: Free tier available

4. **MongoDB URI** (Production)
   - Local: `mongodb://localhost:27017/betslip_converter`
   - Managed: Get from your cloud provider
   - Used for: Data persistence and caching

5. **Redis URL** (Production)
   - Local: `redis://localhost:6379`
   - Managed: Get from your cloud provider
   - Used for: Session storage and caching

### Environment File Example

```bash
# .env file
OPENAI_API_KEY=sk-your-openai-key-here
JWT_SECRET=your-very-secure-jwt-secret-at-least-32-characters
MONGODB_URI=mongodb://localhost:27017/betslip_converter
REDIS_URL=redis://localhost:6379
CORS_ORIGIN=http://localhost:3000
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000
```

## 🧪 Testing Your Deployment

### Health Check
```bash
curl http://localhost/api/health
# Should return: {"status":"healthy","timestamp":"..."}
```

### API Test
```bash
curl -X POST http://localhost/api/convert \
  -H "Content-Type: application/json" \
  -d '{
    "betslipCode": "TEST123",
    "sourceBookmaker": "bet9ja",
    "destinationBookmaker": "sportybet"
  }'
```

### Browser Test
1. Open http://localhost in your browser
2. Enter a test betslip code
3. Select source and destination bookmakers
4. Click "Convert Betslip"

## 📊 Monitoring

### View Logs
```bash
# Docker
docker-compose logs -f app

# Kubernetes (DigitalOcean)
kubectl logs -f deployment/betslip-converter -n betslip-converter

# AWS
aws logs tail /ecs/production-betslip-converter --follow
```

### Health Monitoring
```bash
# Run health checks
./scripts/monitor.sh health

# View system status
./scripts/monitor.sh status

# Analyze logs
./scripts/monitor.sh logs 1h
```

### Metrics Dashboard
- **Docker**: http://localhost:3001 (Grafana)
- **DigitalOcean**: Access via kubectl port-forward
- **AWS**: CloudWatch Dashboard in AWS Console

## 🔒 Security Checklist

### Before Production
- [ ] Change default passwords
- [ ] Use strong JWT secrets
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up monitoring alerts
- [ ] Enable database authentication
- [ ] Review CORS settings
- [ ] Set up backup procedures

### Environment Variables Security
```bash
# Never commit secrets to git
echo ".env*" >> .gitignore

# Use environment-specific files
cp .env.template .env.production
# Edit .env.production with production values

# For Kubernetes, use secrets
kubectl create secret generic betslip-secrets \
  --from-literal=openai-api-key=your-key \
  --from-literal=jwt-secret=your-secret
```

## 🚨 Troubleshooting

### Common Issues

**1. Browser automation fails**
```bash
# Check browser dependencies
docker exec -it betslip-app python3 -c "import playwright; print('OK')"

# Increase timeout
export BROWSER_TIMEOUT=60000
```

**2. Database connection issues**
```bash
# Test MongoDB connection
docker exec -it betslip-mongodb mongosh --eval "db.adminCommand('ping')"

# Check network connectivity
docker exec -it betslip-app nc -zv mongodb 27017
```

**3. High memory usage**
```bash
# Monitor memory
docker stats

# Reduce concurrent browsers
export MAX_CONCURRENT_BROWSERS=2
export MAX_MEMORY_MB=1024
```

**4. SSL certificate issues**
```bash
# Check certificate
openssl x509 -in cert.pem -text -noout

# Test SSL connection
openssl s_client -connect your-domain.com:443
```

### Getting Help

1. **Check logs**: `./scripts/monitor.sh logs`
2. **Run health checks**: `./scripts/monitor.sh health`
3. **Review configuration**: Ensure all required environment variables are set
4. **Check resource usage**: Monitor CPU, memory, and disk usage
5. **Verify network connectivity**: Test database and external API connections

## 📈 Scaling Up

### Performance Optimization
```bash
# Increase resources
export MAX_CONCURRENT_BROWSERS=5
export MAX_MEMORY_MB=4096

# Enable caching
export USE_PARALLEL_PROCESSING=true

# Scale containers
docker-compose up -d --scale app=3
```

### Production Checklist
- [ ] Set up load balancer
- [ ] Configure auto-scaling
- [ ] Implement backup strategy
- [ ] Set up monitoring alerts
- [ ] Configure log aggregation
- [ ] Enable security scanning
- [ ] Set up CI/CD pipeline
- [ ] Document runbooks

## 🔄 Maintenance

### Regular Tasks
```bash
# Update application
git pull
docker-compose build
docker-compose up -d

# Backup data
./scripts/backup.sh

# Clean up old data
./scripts/monitor.sh cleanup

# Update dependencies
npm update
pip install -r requirements.txt --upgrade
```

### Monitoring Schedule
- **Daily**: Check health status and error logs
- **Weekly**: Review performance metrics and resource usage
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Review and test backup/recovery procedures

## 📚 Next Steps

1. **Customize the application** for your specific bookmakers
2. **Set up monitoring and alerting** for production use
3. **Implement CI/CD pipeline** for automated deployments
4. **Add more bookmaker integrations** as needed
5. **Scale infrastructure** based on usage patterns

## 🆘 Support

- **Documentation**: Check the `/docs` directory for detailed guides
- **Issues**: Report bugs and feature requests on GitHub
- **Community**: Join discussions in the project forums
- **Professional Support**: Contact for enterprise support options

---

**Ready to get started?** Choose your deployment option above and follow the steps. The application will be running in minutes!