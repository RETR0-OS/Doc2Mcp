# Deployment Guide

## Docker Deployment

### Building the Image

Create a `Dockerfile`:

```dockerfile
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --production

# Copy built application
COPY dist ./dist

# Create non-root user
RUN addgroup -g 1001 -S doc2mcp && \
    adduser -S doc2mcp -u 1001

# Switch to non-root user
USER doc2mcp

# Run the server
CMD ["node", "dist/index.js"]
```

Build and run:

```bash
npm run build
docker build -t doc2mcp:latest .
docker run -e DOC_URLS="https://api.example.com/openapi.json" doc2mcp:latest
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  doc2mcp:
    build: .
    environment:
      - DOC_URLS=https://petstore.swagger.io/v2/swagger.json
      - TRACING_ENABLED=true
      - ARIZE_ENDPOINT=http://phoenix:6006/v1/traces
    depends_on:
      - phoenix
    restart: unless-stopped

  phoenix:
    image: arizephoenix/phoenix:latest
    ports:
      - "6006:6006"
    restart: unless-stopped
```

Run:

```bash
docker-compose up -d
```

## Kubernetes Deployment

Create `deployment.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: doc2mcp-config
data:
  DOC_URLS: "https://api.example.com/openapi.json"
  TRACING_ENABLED: "true"
  ARIZE_ENDPOINT: "http://phoenix:6006/v1/traces"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: doc2mcp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: doc2mcp
  template:
    metadata:
      labels:
        app: doc2mcp
    spec:
      containers:
      - name: doc2mcp
        image: doc2mcp:latest
        envFrom:
        - configMapRef:
            name: doc2mcp-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: doc2mcp
spec:
  selector:
    app: doc2mcp
  ports:
  - port: 80
    targetPort: 3000
```

Deploy:

```bash
kubectl apply -f deployment.yaml
```

## systemd Service

Create `/etc/systemd/system/doc2mcp.service`:

```ini
[Unit]
Description=Doc2MCP Server
After=network.target

[Service]
Type=simple
User=doc2mcp
Group=doc2mcp
WorkingDirectory=/opt/doc2mcp
ExecStart=/usr/bin/node /opt/doc2mcp/dist/index.js
Environment="DOC_URLS=https://api.example.com/openapi.json"
Environment="TRACING_ENABLED=true"
Environment="ARIZE_ENDPOINT=http://localhost:6006/v1/traces"
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=doc2mcp

[Install]
WantedBy=multi-user.target
```

Setup:

```bash
# Create user
sudo useradd -r -s /bin/false doc2mcp

# Copy files
sudo mkdir -p /opt/doc2mcp
sudo cp -r dist package*.json /opt/doc2mcp/
sudo chown -R doc2mcp:doc2mcp /opt/doc2mcp

# Install dependencies
cd /opt/doc2mcp
sudo -u doc2mcp npm ci --production

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable doc2mcp
sudo systemctl start doc2mcp

# Check status
sudo systemctl status doc2mcp
sudo journalctl -u doc2mcp -f
```

## PM2 Deployment

Install PM2:

```bash
npm install -g pm2
```

Create `ecosystem.config.js`:

```javascript
module.exports = {
  apps: [{
    name: 'doc2mcp',
    script: './dist/index.js',
    instances: 2,
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production',
      DOC_URLS: 'https://api.example.com/openapi.json',
      TRACING_ENABLED: 'true',
      ARIZE_ENDPOINT: 'http://localhost:6006/v1/traces'
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    autorestart: true,
    max_restarts: 10,
    min_uptime: '10s'
  }]
};
```

Deploy:

```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## Nginx Reverse Proxy

If you need to expose Doc2MCP via HTTP:

```nginx
server {
    listen 80;
    server_name doc2mcp.example.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Health Checks

Add health check endpoint (optional enhancement):

```typescript
// In server/index.ts
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    tools: this.tools.size,
    uptime: process.uptime()
  });
});
```

## Monitoring

### Prometheus Metrics

Add to `package.json`:
```json
{
  "dependencies": {
    "prom-client": "^15.0.0"
  }
}
```

### Logging

Use structured logging:

```bash
# JSON logging
export LOG_FORMAT=json

# Log level
export LOG_LEVEL=info
```

## Environment-Specific Configs

### Development
```bash
export NODE_ENV=development
export TRACING_ENABLED=false
```

### Staging
```bash
export NODE_ENV=staging
export TRACING_ENABLED=true
export ARIZE_ENDPOINT=http://staging-phoenix:6006/v1/traces
```

### Production
```bash
export NODE_ENV=production
export TRACING_ENABLED=true
export ARIZE_ENDPOINT=https://phoenix.example.com/v1/traces
export ARIZE_API_KEY=prod-api-key
```

## Security Considerations

1. **Environment Variables**: Never commit secrets to version control
2. **Network Security**: Use TLS for production deployments
3. **User Permissions**: Run as non-root user
4. **Resource Limits**: Set memory and CPU limits
5. **API Keys**: Rotate keys regularly
6. **Rate Limiting**: Implement rate limiting for API calls
