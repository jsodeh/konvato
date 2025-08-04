# Betslip Converter Deployment Guide

This comprehensive guide covers four deployment options for the Betslip Converter application:

1. [LocalStack (Local AWS Simulation)](#localstack-deployment)
2. [Docker (Local/Server)](#docker-deployment)
3. [AWS (Amazon Web Services)](#aws-deployment)
4. [DigitalOcean](#digitalocean-deployment)

## Prerequisites

Before deploying, ensure you have:

- **OpenAI API Key**: Required for browser automation
- **Domain name** (for production deployments)
- **SSL certificates** (for HTTPS)
- **Email service** (for alerts and notifications)

## Quick Start

For immediate testing, use Docker deployment:

```bash
# Clone and setup
git clone <repository-url>
cd betslip-converter
./scripts/setup-environment.sh

# Configure environment
cp .env.template .env
# Edit .env with your API keys

# Deploy with Docker
./scripts/deploy.sh
```

---

## LocalStack Deployment

LocalStack provides a local AWS cloud stack for development and testing.

### Prerequisites

- Docker and Docker Compose
- LocalStack CLI
- AWS CLI configured for LocalStack

### Setup LocalStack

1. **Install LocalStack:**
   ```bash
   pip install localstack
   pip install awscli-local
   ```

2. **Start LocalStack:**
   ```bash
   localstack start -d
   ```

3. **Configure AWS CLI for LocalStack:**
   ```bash
   aws configure set aws_access_key_id test
   aws configure set aws_secret_access_key test
   aws configure set region us-east-1
   aws configure set output json
   ```

### Deploy to LocalStack

1. **Create LocalStack configuration:**
   ```bash
   # Create LocalStack-specific environment file
   cp .env.template .env.localstack
   ```

2. **Configure LocalStack environment:**
   ```bash
   # Edit .env.localstack
   MONGODB_URI=mongodb://localhost:27017/betslip_converter
   AWS_ENDPOINT_URL=http://localhost:4566
   AWS_ACCESS_KEY_ID=test
   AWS_SECRET_ACCESS_KEY=test
   AWS_DEFAULT_REGION=us-east-1
   S3_BUCKET=betslip-converter-local
   ```

3. **Create AWS resources in LocalStack:**
   ```bash
   # Create S3 bucket for file storage
   awslocal s3 mb s3://betslip-converter-local
   
   # Create DynamoDB table for session storage
   awslocal dynamodb create-table \
     --table-name betslip-sessions \
     --attribute-definitions AttributeName=id,AttributeType=S \
     --key-schema AttributeName=id,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST
   
   # Create SQS queue for background jobs
   awslocal sqs create-queue --queue-name betslip-jobs
   ```

4. **Deploy application:**
   ```bash
   # Use LocalStack-specific compose file
   docker-compose -f docker-compose.localstack.yml up -d
   ```

### LocalStack Configuration Files

Create `docker-compose.localstack.yml`:

```yaml
version: '3.8'

services:
  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      - SERVICES=s3,dynamodb,sqs,lambda
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
    volumes:
      - localstack_data:/tmp/localstack
      - /var/run/docker.sock:/var/run/docker.sock

  app:
    extends:
      file: docker-compose.yml
      service: app
    environment:
      - AWS_ENDPOINT_URL=http://localstack:4566
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
    depends_on:
      - localstack
      - mongodb
      - redis

volumes:
  localstack_data:
```

### Testing LocalStack Deployment

```bash
# Test S3 connectivity
awslocal s3 ls s3://betslip-converter-local

# Test application
curl http://localhost/api/health

# View LocalStack logs
docker logs localstack
```

---

## Docker Deployment

Docker deployment is ideal for development, testing, and small-scale production.

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 20GB+ disk space

### Quick Docker Deployment

1. **Setup environment:**
   ```bash
   ./scripts/setup-environment.sh
   ```

2. **Configure environment:**
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

3. **Deploy:**
   ```bash
   ./scripts/deploy.sh
   ```

### Custom Docker Deployment

1. **Build images:**
   ```bash
   docker-compose build
   ```

2. **Start services:**
   ```bash
   # Start core services
   docker-compose up -d mongodb redis
   
   # Wait for databases to initialize
   sleep 30
   
   # Start application
   docker-compose up -d app nginx
   ```

3. **Enable monitoring (optional):**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
   ```

### Docker Configuration Options

#### Development Configuration

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  app:
    extends:
      file: docker-compose.yml
      service: app
    environment:
      - NODE_ENV=development
      - BROWSER_HEADLESS=false
    volumes:
      - ./server:/app/server
      - ./client:/app/client
      - ./automation:/app/automation
    ports:
      - "5000:5000"
      - "9229:9229"  # Debug port
```

#### Production Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    extends:
      file: docker-compose.yml
      service: app
    environment:
      - NODE_ENV=production
      - BROWSER_HEADLESS=true
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

### Docker Maintenance

```bash
# View logs
docker-compose logs -f app

# Scale application
docker-compose up -d --scale app=3

# Update application
docker-compose pull
docker-compose up -d

# Backup data
./scripts/backup.sh

# Monitor health
./scripts/monitor.sh health
```

---

## AWS Deployment

AWS deployment provides scalable, production-ready infrastructure.

### Prerequisites

- AWS CLI configured
- AWS account with appropriate permissions
- Domain name with Route 53 or external DNS
- SSL certificate (ACM or external)

### AWS Architecture

```
Internet Gateway
    ↓
Application Load Balancer (ALB)
    ↓
ECS Fargate Cluster
    ├── Betslip Converter Service
    ├── MongoDB (DocumentDB)
    ├── Redis (ElastiCache)
    └── Monitoring (CloudWatch)
```

### AWS Deployment Steps

1. **Setup AWS CLI:**
   ```bash
   aws configure
   # Enter your AWS credentials and region
   ```

2. **Create AWS infrastructure:**
   ```bash
   # Create deployment directory
   mkdir aws-deployment
   cd aws-deployment
   ```

3. **Deploy using CloudFormation:**

Create `cloudformation-template.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Betslip Converter Infrastructure'

Parameters:
  Environment:
    Type: String
    Default: production
    AllowedValues: [development, staging, production]
  
  DomainName:
    Type: String
    Description: Domain name for the application
  
  CertificateArn:
    Type: String
    Description: SSL certificate ARN

Resources:
  # VPC and Networking
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-betslip-vpc

  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      MapPublicIpOnLaunch: true

  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.3.0/24
      AvailabilityZone: !Select [0, !GetAZs '']

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.4.0/24
      AvailabilityZone: !Select [1, !GetAZs '']

  # Internet Gateway
  InternetGateway:
    Type: AWS::EC2::InternetGateway

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  # Route Tables
  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC

  PublicRoute:
    Type: AWS::EC2::Route
    DependsOn: AttachGateway
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  # Security Groups
  ALBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for Application Load Balancer
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0

  ECSSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for ECS tasks
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 5000
          ToPort: 5000
          SourceSecurityGroupId: !Ref ALBSecurityGroup

  # Application Load Balancer
  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: !Sub ${Environment}-betslip-alb
      Scheme: internet-facing
      Type: application
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
      SecurityGroups:
        - !Ref ALBSecurityGroup

  # ECS Cluster
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: !Sub ${Environment}-betslip-cluster

  # DocumentDB (MongoDB)
  DocumentDBSubnetGroup:
    Type: AWS::DocDB::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Subnet group for DocumentDB
      SubnetIds:
        - !Ref PrivateSubnet1
        - !Ref PrivateSubnet2

  DocumentDBCluster:
    Type: AWS::DocDB::DBCluster
    Properties:
      DBClusterIdentifier: !Sub ${Environment}-betslip-docdb
      MasterUsername: admin
      MasterUserPassword: !Ref DocumentDBPassword
      DBSubnetGroupName: !Ref DocumentDBSubnetGroup
      VpcSecurityGroupIds:
        - !Ref DocumentDBSecurityGroup

  # ElastiCache (Redis)
  ElastiCacheSubnetGroup:
    Type: AWS::ElastiCache::SubnetGroup
    Properties:
      Description: Subnet group for ElastiCache
      SubnetIds:
        - !Ref PrivateSubnet1
        - !Ref PrivateSubnet2

  ElastiCacheCluster:
    Type: AWS::ElastiCache::CacheCluster
    Properties:
      CacheClusterId: !Sub ${Environment}-betslip-redis
      Engine: redis
      CacheNodeType: cache.t3.micro
      NumCacheNodes: 1
      CacheSubnetGroupName: !Ref ElastiCacheSubnetGroup
      VpcSecurityGroupIds:
        - !Ref ElastiCacheSecurityGroup

Outputs:
  LoadBalancerDNS:
    Description: DNS name of the load balancer
    Value: !GetAtt ApplicationLoadBalancer.DNSName
    Export:
      Name: !Sub ${Environment}-betslip-alb-dns
```

4. **Deploy CloudFormation stack:**
   ```bash
   aws cloudformation create-stack \
     --stack-name betslip-converter-infrastructure \
     --template-body file://cloudformation-template.yaml \
     --parameters ParameterKey=Environment,ParameterValue=production \
                  ParameterKey=DomainName,ParameterValue=your-domain.com \
                  ParameterKey=CertificateArn,ParameterValue=arn:aws:acm:... \
     --capabilities CAPABILITY_IAM
   ```

5. **Deploy application to ECS:**

Create `ecs-task-definition.json`:

```json
{
  "family": "betslip-converter",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "betslip-app",
      "image": "your-account.dkr.ecr.region.amazonaws.com/betslip-converter:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "NODE_ENV",
          "value": "production"
        },
        {
          "name": "MONGODB_URI",
          "value": "mongodb://admin:password@docdb-cluster-endpoint:27017/betslip_converter"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://elasticache-endpoint:6379"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/betslip-converter",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

6. **Register task definition and create service:**
   ```bash
   # Register task definition
   aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
   
   # Create ECS service
   aws ecs create-service \
     --cluster betslip-converter-cluster \
     --service-name betslip-converter-service \
     --task-definition betslip-converter:1 \
     --desired-count 2 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
   ```

### AWS Monitoring and Scaling

1. **CloudWatch monitoring:**
   ```bash
   # Create CloudWatch dashboard
   aws cloudwatch put-dashboard \
     --dashboard-name "BetslipConverter" \
     --dashboard-body file://cloudwatch-dashboard.json
   ```

2. **Auto Scaling:**
   ```bash
   # Create auto scaling target
   aws application-autoscaling register-scalable-target \
     --service-namespace ecs \
     --resource-id service/betslip-converter-cluster/betslip-converter-service \
     --scalable-dimension ecs:service:DesiredCount \
     --min-capacity 2 \
     --max-capacity 10
   ```

### AWS Costs Optimization

- Use Spot instances for development
- Implement proper auto-scaling policies
- Use CloudWatch for monitoring and alerting
- Regular cost analysis with AWS Cost Explorer

---

## DigitalOcean Deployment

DigitalOcean provides simple, cost-effective cloud infrastructure.

### Prerequisites

- DigitalOcean account
- `doctl` CLI tool
- Docker registry access
- Domain name

### DigitalOcean Architecture

```
Load Balancer
    ↓
Kubernetes Cluster (DOKS)
    ├── Betslip Converter Pods
    ├── MongoDB (Managed Database)
    ├── Redis (Managed Database)
    └── Monitoring Stack
```

### Setup DigitalOcean

1. **Install doctl:**
   ```bash
   # macOS
   brew install doctl
   
   # Linux
   wget https://github.com/digitalocean/doctl/releases/download/v1.94.0/doctl-1.94.0-linux-amd64.tar.gz
   tar xf doctl-1.94.0-linux-amd64.tar.gz
   sudo mv doctl /usr/local/bin
   ```

2. **Authenticate:**
   ```bash
   doctl auth init
   # Enter your DigitalOcean API token
   ```

3. **Create infrastructure:**
   ```bash
   # Create Kubernetes cluster
   doctl kubernetes cluster create betslip-converter \
     --region nyc1 \
     --version 1.28.2-do.0 \
     --count 3 \
     --size s-2vcpu-2gb \
     --auto-upgrade=true \
     --maintenance-window="saturday=06:00"
   
   # Create managed MongoDB
   doctl databases create betslip-mongodb \
     --engine mongodb \
     --region nyc1 \
     --size db-s-1vcpu-1gb \
     --num-nodes 1
   
   # Create managed Redis
   doctl databases create betslip-redis \
     --engine redis \
     --region nyc1 \
     --size db-s-1vcpu-1gb \
     --num-nodes 1
   ```

### Kubernetes Deployment

1. **Configure kubectl:**
   ```bash
   doctl kubernetes cluster kubeconfig save betslip-converter
   ```

2. **Create namespace:**
   ```bash
   kubectl create namespace betslip-converter
   ```

3. **Create secrets:**
   ```bash
   kubectl create secret generic betslip-secrets \
     --from-literal=openai-api-key=your-openai-key \
     --from-literal=jwt-secret=your-jwt-secret \
     --namespace=betslip-converter
   ```

4. **Deploy application:**

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: betslip-converter
  namespace: betslip-converter
spec:
  replicas: 3
  selector:
    matchLabels:
      app: betslip-converter
  template:
    metadata:
      labels:
        app: betslip-converter
    spec:
      containers:
      - name: betslip-app
        image: registry.digitalocean.com/your-registry/betslip-converter:latest
        ports:
        - containerPort: 5000
        env:
        - name: NODE_ENV
          value: "production"
        - name: MONGODB_URI
          value: "mongodb://username:password@managed-db-host:27017/betslip_converter"
        - name: REDIS_URL
          value: "redis://managed-redis-host:25061"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: betslip-secrets
              key: openai-api-key
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: betslip-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: betslip-converter-service
  namespace: betslip-converter
spec:
  selector:
    app: betslip-converter
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: betslip-converter-ingress
  namespace: betslip-converter
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: betslip-converter-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: betslip-converter-service
            port:
              number: 80
```

5. **Apply Kubernetes manifests:**
   ```bash
   kubectl apply -f k8s-deployment.yaml
   ```

6. **Create load balancer:**
   ```bash
   doctl compute load-balancer create \
     --name betslip-converter-lb \
     --region nyc1 \
     --forwarding-rules entry_protocol:https,entry_port:443,target_protocol:http,target_port:80,certificate_id:your-cert-id \
     --health-check protocol:http,port:80,path:/api/health,check_interval_seconds:10,response_timeout_seconds:5,healthy_threshold:3,unhealthy_threshold:3 \
     --tag-name k8s:betslip-converter
   ```

### DigitalOcean Monitoring

1. **Enable monitoring:**
   ```bash
   # Install monitoring agent on nodes
   kubectl apply -f https://raw.githubusercontent.com/digitalocean/do-agent/master/k8s/do-agent.yaml
   ```

2. **Setup Prometheus monitoring:**

Create `monitoring-stack.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: prometheus-config
          mountPath: /etc/prometheus
        - name: prometheus-storage
          mountPath: /prometheus
      volumes:
      - name: prometheus-config
        configMap:
          name: prometheus-config
      - name: prometheus-storage
        persistentVolumeClaim:
          claimName: prometheus-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: prometheus-service
  namespace: monitoring
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090
  type: LoadBalancer
```

### DigitalOcean Maintenance

```bash
# Scale application
kubectl scale deployment betslip-converter --replicas=5 -n betslip-converter

# Update application
kubectl set image deployment/betslip-converter betslip-app=registry.digitalocean.com/your-registry/betslip-converter:v2 -n betslip-converter

# Monitor deployment
kubectl rollout status deployment/betslip-converter -n betslip-converter

# View logs
kubectl logs -f deployment/betslip-converter -n betslip-converter

# Create database backup
doctl databases backups list betslip-mongodb
```

### DigitalOcean Cost Optimization

- Use appropriate droplet sizes
- Implement horizontal pod autoscaling
- Use managed databases for reliability
- Regular monitoring of resource usage
- Implement proper resource requests and limits

---

## Comparison Matrix

| Feature | LocalStack | Docker | AWS | DigitalOcean |
|---------|------------|--------|-----|--------------|
| **Cost** | Free | Low | Variable | Medium |
| **Complexity** | Medium | Low | High | Medium |
| **Scalability** | Limited | Limited | High | High |
| **Production Ready** | No | Limited | Yes | Yes |
| **Monitoring** | Basic | Good | Excellent | Good |
| **Maintenance** | Low | Medium | High | Medium |
| **Learning Curve** | Medium | Low | High | Medium |

## Security Considerations

### All Deployments

1. **Environment Variables:**
   - Never commit secrets to version control
   - Use secure secret management
   - Rotate API keys regularly

2. **Network Security:**
   - Use HTTPS/TLS encryption
   - Implement proper firewall rules
   - Use VPCs/private networks

3. **Database Security:**
   - Enable authentication
   - Use encrypted connections
   - Regular security updates

4. **Application Security:**
   - Input validation
   - Rate limiting
   - Security headers

### Production-Specific

1. **SSL/TLS:**
   - Use valid SSL certificates
   - Implement HSTS
   - Regular certificate renewal

2. **Monitoring:**
   - Security event logging
   - Intrusion detection
   - Regular security audits

3. **Backup and Recovery:**
   - Automated backups
   - Disaster recovery plan
   - Regular restore testing

## Troubleshooting

### Common Issues

1. **Browser Automation Failures:**
   ```bash
   # Check browser dependencies
   docker exec -it betslip-app python3 -c "import playwright; print('OK')"
   
   # Increase timeout values
   export BROWSER_TIMEOUT=60000
   ```

2. **Database Connection Issues:**
   ```bash
   # Test MongoDB connection
   docker exec -it betslip-mongodb mongosh --eval "db.adminCommand('ping')"
   
   # Check network connectivity
   docker exec -it betslip-app nc -zv mongodb 27017
   ```

3. **Memory Issues:**
   ```bash
   # Monitor memory usage
   docker stats
   
   # Increase memory limits
   docker-compose up -d --scale app=1 --memory=4g
   ```

4. **SSL Certificate Issues:**
   ```bash
   # Check certificate validity
   openssl x509 -in cert.pem -text -noout
   
   # Test SSL connection
   openssl s_client -connect your-domain.com:443
   ```

### Getting Help

- Check application logs: `./scripts/monitor.sh logs`
- Run health checks: `./scripts/monitor.sh health`
- Review monitoring dashboards
- Check official documentation
- Community support forums

---

## Next Steps

After successful deployment:

1. **Configure monitoring and alerting**
2. **Set up automated backups**
3. **Implement CI/CD pipeline**
4. **Performance optimization**
5. **Security hardening**
6. **Load testing**
7. **Documentation updates**

For detailed configuration options and advanced features, refer to the specific deployment guides in the `/docs` directory.