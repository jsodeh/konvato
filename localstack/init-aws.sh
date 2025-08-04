#!/bin/bash

# LocalStack AWS resources initialization script
# This script creates the necessary AWS resources in LocalStack

set -e

echo "Waiting for LocalStack to be ready..."
sleep 10

# Set LocalStack endpoint
export AWS_ENDPOINT_URL=http://localstack:4566

echo "Creating S3 bucket for file storage..."
aws s3 mb s3://betslip-converter-local --endpoint-url=$AWS_ENDPOINT_URL || echo "Bucket already exists"

# Set bucket policy for public read access to static files
aws s3api put-bucket-policy --bucket betslip-converter-local --endpoint-url=$AWS_ENDPOINT_URL --policy '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::betslip-converter-local/public/*"
    }
  ]
}'

echo "Creating DynamoDB table for session storage..."
aws dynamodb create-table \
  --table-name betslip-sessions \
  --attribute-definitions \
    AttributeName=sessionId,AttributeType=S \
    AttributeName=userId,AttributeType=S \
  --key-schema \
    AttributeName=sessionId,KeyType=HASH \
  --global-secondary-indexes \
    IndexName=UserIndex,KeySchema=[{AttributeName=userId,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --endpoint-url=$AWS_ENDPOINT_URL || echo "Table already exists"

echo "Creating DynamoDB table for conversion cache..."
aws dynamodb create-table \
  --table-name betslip-conversion-cache \
  --attribute-definitions \
    AttributeName=cacheKey,AttributeType=S \
  --key-schema \
    AttributeName=cacheKey,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=10 \
  --time-to-live-specification AttributeName=ttl,Enabled=true \
  --endpoint-url=$AWS_ENDPOINT_URL || echo "Table already exists"

echo "Creating SQS queue for background jobs..."
aws sqs create-queue \
  --queue-name betslip-jobs \
  --attributes VisibilityTimeoutSeconds=300,MessageRetentionPeriod=1209600 \
  --endpoint-url=$AWS_ENDPOINT_URL || echo "Queue already exists"

echo "Creating SQS dead letter queue..."
aws sqs create-queue \
  --queue-name betslip-jobs-dlq \
  --endpoint-url=$AWS_ENDPOINT_URL || echo "DLQ already exists"

echo "Creating Secrets Manager secrets..."
aws secretsmanager create-secret \
  --name betslip-converter/openai-api-key \
  --description "OpenAI API key for browser automation" \
  --secret-string "${OPENAI_API_KEY:-test-key}" \
  --endpoint-url=$AWS_ENDPOINT_URL || echo "Secret already exists"

aws secretsmanager create-secret \
  --name betslip-converter/jwt-secret \
  --description "JWT secret for token signing" \
  --secret-string "${JWT_SECRET:-test-jwt-secret-change-in-production}" \
  --endpoint-url=$AWS_ENDPOINT_URL || echo "Secret already exists"

aws secretsmanager create-secret \
  --name betslip-converter/database-credentials \
  --description "Database connection credentials" \
  --secret-string '{"username":"admin","password":"password","host":"mongodb","port":"27017","database":"betslip_converter"}' \
  --endpoint-url=$AWS_ENDPOINT_URL || echo "Secret already exists"

echo "Creating CloudWatch log groups..."
aws logs create-log-group \
  --log-group-name /aws/lambda/betslip-converter \
  --endpoint-url=$AWS_ENDPOINT_URL || echo "Log group already exists"

aws logs create-log-group \
  --log-group-name /betslip-converter/application \
  --endpoint-url=$AWS_ENDPOINT_URL || echo "Log group already exists"

echo "Setting up CloudWatch metrics..."
aws cloudwatch put-metric-data \
  --namespace "BetslipConverter/Test" \
  --metric-data MetricName=InitializationComplete,Value=1,Unit=Count \
  --endpoint-url=$AWS_ENDPOINT_URL

echo "Creating Lambda function for background processing..."
# Create a simple Lambda function for demonstration
cat > /tmp/lambda-function.py << 'EOF'
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Background job processor for betslip conversion tasks
    """
    logger.info(f"Processing event: {json.dumps(event)}")
    
    # Process the conversion job
    try:
        # Simulate processing
        job_id = event.get('jobId', 'unknown')
        job_type = event.get('jobType', 'conversion')
        
        logger.info(f"Processing job {job_id} of type {job_type}")
        
        # Here you would implement actual job processing logic
        result = {
            'jobId': job_id,
            'status': 'completed',
            'message': 'Job processed successfully'
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error processing job: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
EOF

# Create deployment package
cd /tmp
zip lambda-function.zip lambda-function.py

# Create Lambda function
aws lambda create-function \
  --function-name betslip-background-processor \
  --runtime python3.9 \
  --role arn:aws:iam::000000000000:role/lambda-execution-role \
  --handler lambda-function.lambda_handler \
  --zip-file fileb://lambda-function.zip \
  --description "Background processor for betslip conversion jobs" \
  --timeout 300 \
  --memory-size 512 \
  --endpoint-url=$AWS_ENDPOINT_URL || echo "Lambda function already exists"

echo "Creating IAM role for Lambda (LocalStack simulation)..."
aws iam create-role \
  --role-name lambda-execution-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }' \
  --endpoint-url=$AWS_ENDPOINT_URL || echo "Role already exists"

echo "Setting up SQS trigger for Lambda..."
aws lambda create-event-source-mapping \
  --event-source-arn arn:aws:sqs:us-east-1:000000000000:betslip-jobs \
  --function-name betslip-background-processor \
  --batch-size 10 \
  --endpoint-url=$AWS_ENDPOINT_URL || echo "Event source mapping already exists"

echo "Creating sample data in S3..."
echo "Welcome to Betslip Converter LocalStack Demo" > /tmp/welcome.txt
aws s3 cp /tmp/welcome.txt s3://betslip-converter-local/public/welcome.txt --endpoint-url=$AWS_ENDPOINT_URL

echo "Creating CloudWatch dashboard..."
aws cloudwatch put-dashboard \
  --dashboard-name "BetslipConverter-LocalStack" \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "x": 0,
        "y": 0,
        "width": 12,
        "height": 6,
        "properties": {
          "metrics": [
            [ "BetslipConverter", "ConversionRequests" ],
            [ ".", "ConversionErrors" ],
            [ ".", "ConversionLatency" ]
          ],
          "period": 300,
          "stat": "Sum",
          "region": "us-east-1",
          "title": "Betslip Conversion Metrics"
        }
      }
    ]
  }' \
  --endpoint-url=$AWS_ENDPOINT_URL || echo "Dashboard already exists"

echo "LocalStack AWS resources initialization completed successfully!"

# Test the setup
echo "Testing S3 access..."
aws s3 ls s3://betslip-converter-local --endpoint-url=$AWS_ENDPOINT_URL

echo "Testing DynamoDB access..."
aws dynamodb list-tables --endpoint-url=$AWS_ENDPOINT_URL

echo "Testing SQS access..."
aws sqs list-queues --endpoint-url=$AWS_ENDPOINT_URL

echo "Testing Secrets Manager access..."
aws secretsmanager list-secrets --endpoint-url=$AWS_ENDPOINT_URL

echo "All AWS resources are ready for use!"

# Create a test message in SQS
echo "Sending test message to SQS..."
aws sqs send-message \
  --queue-url http://localstack:4566/000000000000/betslip-jobs \
  --message-body '{"jobId":"test-001","jobType":"conversion","betslipCode":"TEST123","sourceBookmaker":"bet9ja","destinationBookmaker":"sportybet"}' \
  --endpoint-url=$AWS_ENDPOINT_URL

echo "LocalStack initialization complete!"