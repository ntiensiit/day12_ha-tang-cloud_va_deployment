# Day 12 Lab - Mission Answers

> **Student Name:** Nguyễn Tiến Sỉ
> **Student ID:** 2A202600681
> **Date:** 12/06/2026

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. **In-memory state management** (`conversation_history = {}`): This prevents horizontal scaling as different request instances will lack user history.
2. **Missing health and readiness check configurations**: The application has no endpoints (`/healthz`, `/readyz`) to notify container orchestrators (like Kubernetes or Railway) whether it can receive traffic or if it should be restarted.
3. **Absence of signal handling/graceful shutdown**: The application terminates instantly upon receiving a `SIGTERM`, severing active client requests and leaving database/Redis connections dangling.
4. **Hardcoded configuration values and credentials**: Secrets and addresses are hardcoded in source files instead of loading from environment variables or a configuration manager.

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---|---|---|---|
| Config | Hardcoded / `.env` local | Env variables / Vault | Security & Flexibility across different environment targets |
| Logs | Console stdout prints | Structured JSON logs | Traceability, parsing and querying logs centrally (e.g. Datadog, ELK) |
| Scaling | Single process | Multi-instance with Load Balancer | High availability, performance, and fault tolerance |
| State | Memory | Redis / Database | Allows horizontal scalability and node-failover robustness |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image**: `python:3.11-slim`
2. **Working directory**: `/app`

### Exercise 2.3: Image size comparison
- Develop: [INSERT DEVELOPMENT IMAGE SIZE, e.g. 950] MB
- Production: [INSERT PRODUCTION IMAGE SIZE, e.g. 210] MB
- Difference: [INSERT DIFFERENCE PERCENTAGE, e.g. 77]% reduction

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://my-production-agent-latest.onrender.com
- Screenshot: [SCREENSHOT IN REPO](screenshots/repo.png)

## Part 4: API Security

### Exercise 4.1-4.3: Test results
- Auth validation (Unauthorized): HTTP 401 response when token is missing or incorrect.
- Rate limiter: HTTP 429 response when requests exceed 10 requests per minute.

### Exercise 4.4: Cost guard implementation
- Approach: We track and persist monthly usage metrics for each user in Redis with a structured key (e.g. `cost:user_id:YYYYMM`). Each request increments the usage (based on simulated cost per request) via `incrbyfloat`. If the monthly usage reaches or exceeds the threshold (e.g. $10), the server returns HTTP 402 Payment Required.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
- **Graceful shutdown**: Handled by interception of `SIGTERM`/`SIGINT` signals, setting a thread-safe shutdown event, stopping acceptance of new HTTP requests, allowing 2-second default buffer for in-flight requests, and exiting cleanly with status `0`.
- **Stateless design**: Refactored the local memory caching to standard Redis list calls (`lrange`, `rpush`, `ltrim`) to keep state centralized, facilitating multi-container scaling.
