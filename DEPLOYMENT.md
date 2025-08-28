# Render Deployment Guide

## After Blueprint Deployment

Once your services are deployed via Blueprint, you'll need to manually set these environment variables in the Render dashboard:

### Backend Service (konvato-server)
1. Go to `konvato-server` service in Render dashboard
2. Navigate to Environment tab
3. Add these variables:

```bash
# Required API Keys (at least one)
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Custom URLs (defaults will work if not set)
AUTOMATION_SERVICE_URL=https://konvato-automation.onrender.com
CORS_ORIGIN=https://konvato-client.onrender.com
```

### Automation Service (konvato-automation)
1. Go to `konvato-automation` service in Render dashboard
2. Navigate to Environment tab
3. Add these variables:

```bash
# Required API Keys (same as backend)
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Service URLs

After deployment, your services will be available at:

- **Frontend**: `https://konvato-client.onrender.com`
- **Backend API**: `https://konvato-server.onrender.com`
- **Health Check**: `https://konvato-server.onrender.com/health`

## Testing

1. Visit your frontend URL
2. Try the `/health` endpoint on your backend
3. Test a betslip conversion through the UI

## Troubleshooting

- Check service logs in Render dashboard
- Verify all environment variables are set
- Ensure services are all running (green status)
- Check CORS configuration if frontend can't reach backend