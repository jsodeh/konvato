# Betslip Converter API Documentation

## Overview

The Betslip Converter API provides programmatic access to betslip conversion functionality. This RESTful API allows developers to integrate betslip conversion capabilities into their applications.

## Base URL

```
Production: https://api.betslip-converter.com
Development: http://localhost:5000
```

## Authentication

Currently, the API does not require authentication. Rate limiting is applied to prevent abuse.

## Rate Limiting

- **Conversion Endpoint**: 10 requests per minute per IP address
- **Other Endpoints**: 60 requests per minute per IP address

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Error Handling

The API uses standard HTTP status codes and returns JSON error responses:

```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE",
  "requestId": "req_1234567890_abcdef"
}
```

### Common Error Codes

- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INVALID_INPUT`: Invalid request parameters
- `TIMEOUT`: Request timed out
- `SCRIPT_ERROR`: Browser automation failed
- `PARSE_ERROR`: Failed to parse automation result
- `UNKNOWN_ERROR`: Unexpected error occurred

## Endpoints

### POST /api/convert

Convert a betslip from one bookmaker to another.

#### Request

```http
POST /api/convert
Content-Type: application/json

{
  "betslipCode": "ABC123XYZ",
  "sourceBookmaker": "bet9ja",
  "destinationBookmaker": "sportybet"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `betslipCode` | string | Yes | Alphanumeric betslip code (3-50 characters) |
| `sourceBookmaker` | string | Yes | Source bookmaker ID |
| `destinationBookmaker` | string | Yes | Destination bookmaker ID |

#### Supported Bookmakers

- `bet9ja` - Bet9ja
- `sportybet` - Sportybet  
- `betway` - Betway
- `bet365` - Bet365

#### Response

```json
{
  "success": true,
  "betslipCode": "XYZ789ABC",
  "selections": [
    {
      "game": "Manchester United vs Liverpool",
      "market": "Match Result - Home Win",
      "odds": 2.45,
      "originalOdds": 2.50,
      "status": "converted"
    }
  ],
  "warnings": [],
  "processingTime": 15420,
  "partialConversion": false,
  "timestamp": "2024-01-15T10:30:00.000Z",
  "stats": {
    "totalSelections": 1,
    "convertedSelections": 1,
    "partialSelections": 0,
    "unavailableSelections": 0
  },
  "disclaimers": [
    "Converted betslips are provided as-is. Always verify before placing bets.",
    "Odds may change between conversion and bet placement."
  ],
  "requestId": "req_1234567890_abcdef"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether conversion was successful |
| `betslipCode` | string | New betslip code for destination bookmaker |
| `selections` | array | Array of converted betting selections |
| `warnings` | array | Array of warning messages |
| `processingTime` | number | Processing time in milliseconds |
| `partialConversion` | boolean | Whether some selections couldn't be converted |
| `timestamp` | string | ISO timestamp of conversion |
| `stats` | object | Conversion statistics |
| `disclaimers` | array | Legal disclaimers |
| `requestId` | string | Unique request identifier |

#### Selection Object

| Field | Type | Description |
|-------|------|-------------|
| `game` | string | Game/match name |
| `market` | string | Betting market |
| `odds` | number | Odds on destination bookmaker |
| `originalOdds` | number | Original odds from source bookmaker |
| `status` | string | Conversion status: `converted`, `partial`, `unavailable` |

#### Error Response

```json
{
  "success": false,
  "error": "Invalid betslip code format. Must be alphanumeric, 3-50 characters",
  "code": "INVALID_INPUT",
  "requestId": "req_1234567890_abcdef"
}
```

### GET /api/bookmakers

Get list of supported bookmakers.

#### Request

```http
GET /api/bookmakers
```

#### Response

```json
{
  "bookmakers": [
    {
      "id": "bet9ja",
      "name": "Bet9ja",
      "supported": true,
      "cached": true
    },
    {
      "id": "sportybet", 
      "name": "Sportybet",
      "supported": true,
      "cached": true
    }
  ]
}
```

### GET /api/health

Check API health status.

#### Request

```http
GET /api/health
```

#### Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "services": {
    "api": "healthy",
    "cache": "healthy"
  }
}
```

### GET /api/metrics

Get Prometheus-compatible metrics (monitoring).

#### Request

```http
GET /api/metrics
```

#### Response

```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="POST",route="/api/convert",status="200"} 1234

# HELP conversion_duration_seconds Duration of betslip conversions
# TYPE conversion_duration_seconds histogram
conversion_duration_seconds_bucket{source_bookmaker="bet9ja",destination_bookmaker="sportybet",le="5"} 100
```

## SDK Examples

### JavaScript/Node.js

```javascript
const axios = require('axios');

async function convertBetslip(betslipCode, sourceBookmaker, destinationBookmaker) {
  try {
    const response = await axios.post('http://localhost:5000/api/convert', {
      betslipCode,
      sourceBookmaker,
      destinationBookmaker
    });
    
    return response.data;
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.error);
    }
    throw error;
  }
}

// Usage
convertBetslip('ABC123XYZ', 'bet9ja', 'sportybet')
  .then(result => {
    console.log('New betslip code:', result.betslipCode);
    console.log('Converted selections:', result.selections.length);
  })
  .catch(error => {
    console.error('Conversion failed:', error.message);
  });
```

### Python

```python
import requests
import json

def convert_betslip(betslip_code, source_bookmaker, destination_bookmaker):
    url = 'http://localhost:5000/api/convert'
    payload = {
        'betslipCode': betslip_code,
        'sourceBookmaker': source_bookmaker,
        'destinationBookmaker': destination_bookmaker
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {e}")

# Usage
try:
    result = convert_betslip('ABC123XYZ', 'bet9ja', 'sportybet')
    print(f"New betslip code: {result['betslipCode']}")
    print(f"Converted selections: {len(result['selections'])}")
except Exception as e:
    print(f"Conversion failed: {e}")
```

### cURL

```bash
# Convert betslip
curl -X POST http://localhost:5000/api/convert \
  -H "Content-Type: application/json" \
  -d '{
    "betslipCode": "ABC123XYZ",
    "sourceBookmaker": "bet9ja", 
    "destinationBookmaker": "sportybet"
  }'

# Get supported bookmakers
curl http://localhost:5000/api/bookmakers

# Check health
curl http://localhost:5000/api/health
```

## Webhooks (Future Feature)

Webhooks will be available in a future version to notify your application when conversions complete.

```json
{
  "event": "conversion.completed",
  "data": {
    "requestId": "req_1234567890_abcdef",
    "success": true,
    "betslipCode": "XYZ789ABC",
    "processingTime": 15420
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## Best Practices

### Error Handling
- Always check the `success` field in responses
- Implement retry logic for timeout errors
- Handle rate limiting gracefully with exponential backoff

### Performance
- Cache bookmaker lists locally
- Implement request timeouts (30-60 seconds)
- Use connection pooling for multiple requests

### Security
- Validate input parameters before sending requests
- Don't log sensitive betslip codes
- Use HTTPS in production

### Monitoring
- Track conversion success rates
- Monitor response times
- Set up alerts for error rates

## Compliance

### Data Privacy
- Betslip codes are not stored permanently
- All data is encrypted in transit
- Session data expires after 24 hours

### Rate Limiting
- Respect rate limits to ensure service availability
- Implement proper backoff strategies
- Contact support for higher rate limits if needed

### Legal Compliance
- Users are responsible for complying with local laws
- Service respects bookmaker terms of service
- Gambling disclaimers apply to all conversions

## Support

### API Status
Monitor API status and planned maintenance:
- Status page: `/health`
- Metrics: `/api/metrics`

### Contact
- Technical issues: Check error codes and retry
- Rate limit increases: Contact support
- Feature requests: Submit via GitHub issues

### Changelog
- v1.0.0: Initial API release
- v1.1.0: Added metrics endpoint
- v1.2.0: Enhanced error handling

---

*API Version: 1.2.0*
*Last Updated: January 2024*