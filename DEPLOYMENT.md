# Deployment Information

## Public URL
https://my-production-agent-latest.onrender.com

## Platform
Render

## Test Commands

### Health Check
```bash
curl https://my-production-agent-latest.onrender.com/health
```

### Readiness Check
```bash
curl https://my-production-agent-latest.onrender.com/ready
```

### API Test (with authentication)
```bash
curl -X POST https://my-production-agent-latest.onrender.com/ask \
  -H "X-API-Key: admin-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "question": "Hello Agent!"}'
```

## Environment Variables Set
- `PORT`: 8000
- `REDIS_HOST`: Name of the Redis host instance (e.g., redis connection endpoint)
- `REDIS_PORT`: 6379
- `API_KEY`: Secret key used for HTTP header authorization validation
- `RATE_LIMIT_PER_MIN`: 10
- `MONTHLY_COST_LIMIT_USD`: 10.0

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)
