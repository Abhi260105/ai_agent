Production Deployment Guide
Overview
This document provides comprehensive instructions for deploying the application to production environments using various deployment strategies and platforms.
Pre-Deployment Checklist
Code Quality

 All tests passing (unit, integration, e2e)
 Code reviewed and approved
 Security scan completed
 Performance benchmarks met
 Documentation updated

Configuration

 Environment variables configured
 Secrets properly stored
 Database migrations tested
 Feature flags configured
 Monitoring and logging setup

Infrastructure

 SSL certificates obtained
 DNS records configured
 Load balancers configured
 CDN configured
 Backup systems tested

Deployment Strategies
Blue-Green Deployment
┌─────────────────┐
│  Load Balancer  │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│ Blue  │ │ Green │
│ (Old) │ │ (New) │
└───────┘ └───────┘
Steps:

Deploy new version to Green environment
Run smoke tests on Green
Gradually shift traffic from Blue to Green
Monitor metrics and errors
Rollback to Blue if issues detected
Keep Blue for one release cycle

Implementation:
bash# Deploy to Green
./deploy.sh green

# Health check
curl https://green.example.com/health

# Switch traffic (gradually)
./traffic-shift.sh --from blue --to green --percent 10
./traffic-shift.sh --from blue --to green --percent 50
./traffic-shift.sh --from blue --to green --percent 100

# Decommission Blue (after verification)
./decommission.sh blue
Rolling Deployment
Gradually replace old instances with new ones.
bash# Update instances one at a time
for instance in $(get_instances); do
    drain_connections $instance
    deploy_new_version $instance
    health_check $instance
    restore_traffic $instance
    sleep 60  # Wait between instances
done
Canary Deployment
Deploy to small subset first, then expand.
┌─────────────────┐
│  Load Balancer  │
└────────┬────────┘
         │
    ┌────┴────────────┐
    ▼                 ▼
┌────────┐      ┌──────────┐
│Stable  │      │ Canary   │
│ (95%)  │      │  (5%)    │
└────────┘      └──────────┘
Steps:

Deploy to 5% of servers
Monitor for 1-4 hours
Gradually increase to 25%, 50%, 100%
Rollback if errors exceed threshold

Platform-Specific Deployment
AWS Deployment
Using Elastic Beanstalk
bash# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 my-app --region us-east-1

# Create environment
eb create production-env \
    --instance-type t3.medium \
    --scale 2,10 \
    --database.engine postgres

# Deploy
eb deploy production-env

# Monitor
eb health production-env
eb logs production-env
Using ECS (Fargate)
yaml# task-definition.json
{
  "family": "my-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/my-app:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "NODE_ENV", "value": "production"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/my-app",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
bash# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Update service
aws ecs update-service \
    --cluster production \
    --service my-app \
    --task-definition my-app:1

# Monitor deployment
aws ecs wait services-stable \
    --cluster production \
    --services my-app
Google Cloud Deployment
Using Cloud Run
bash# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/my-app

# Deploy
gcloud run deploy my-app \
    --image gcr.io/PROJECT_ID/my-app \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --min-instances 2 \
    --max-instances 100

# Monitor
gcloud run services describe my-app \
    --platform managed \
    --region us-central1
Using GKE (Kubernetes)
yaml# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: app
        image: gcr.io/PROJECT_ID/my-app:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: my-app-service
spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
    bash# Apply configuration
kubectl apply -f deployment.yaml

# Check status
kubectl get deployments
kubectl get pods
kubectl get services

# Monitor rollout
kubectl rollout status deployment/my-app

# Scale
kubectl scale deployment my-app --replicas=5

# Rollback
kubectl rollout undo deployment/my-app
Kubernetes Deployment
Complete Production Setup
yaml# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production

---
# config-map.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
data:
  LOG_LEVEL: "info"
  MAX_CONNECTIONS: "100"

---
# secret.yaml (encrypted in practice)
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: production
type: Opaque
stringData:
  database-url: "postgresql://user:pass@host:5432/db"
  api-key: "secret-api-key"

---
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: production
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
        version: "1.0.0"
    spec:
      containers:
      - name: app
        image: my-app:1.0.0
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
          name: http
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - my-app
              topologyKey: kubernetes.io/hostname

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  namespace: production
spec:
  type: ClusterIP
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  namespace: production
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - example.com
    secretName: example-com-tls
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app
            port:
              number: 80

---
# hpa.yaml (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

CI/CD Pipeline
GitHub Actions
yaml# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  DOCKER_REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run tests
        run: |
          docker-compose run --rm app pytest
      
      - name: Run linters
        run: |
          docker-compose run --rm app flake8 .
  
  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v3
      
      - name: Log in to registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.DOCKER_REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            ${{ env.DOCKER_REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.DOCKER_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
      
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/my-app \
            app=${{ env.DOCKER_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
            -n production
          kubectl rollout status deployment/my-app -n production
      
      - name: Verify deployment
        run: |
          kubectl get pods -n production
          kubectl get services -n production
Database Migrations
Pre-Deployment
bash# Backup database
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Test migrations in staging
./manage.py migrate --database=staging --plan

# Dry run
./manage.py migrate --database=production --plan
During Deployment
bash# Run migrations
./manage.py migrate --database=production

# Verify
./manage.py showmigrations
Rollback Plan
bash# Rollback migration
./manage.py migrate app_name migration_name

# Restore from backup if needed
gunzip < backup_20260211_120000.sql.gz | psql -h $DB_HOST -U $DB_USER $DB_NAME
Monitoring
Health Checks
python@app.route('/health')
def health():
    """Basic health check."""
    return {'status': 'healthy'}, 200

@app.route('/ready')
def ready():
    """Readiness check with dependencies."""
    checks = {
        'database': check_database(),
        'redis': check_redis(),
        'external_api': check_external_api()
    }
    
    if all(checks.values()):
        return {'status': 'ready', 'checks': checks}, 200
    else:
        return {'status': 'not_ready', 'checks': checks}, 503
Metrics
pythonfrom prometheus_client import Counter, Histogram, Gauge

request_count = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
active_users = Gauge('active_users', 'Number of active users')
Rollback Procedures
Quick Rollback
bash# Kubernetes
kubectl rollout undo deployment/my-app -n production

# ECS
aws ecs update-service \
    --cluster production \
    --service my-app \
    --task-definition my-app:PREVIOUS_VERSION

# Elastic Beanstalk
eb deploy production-env --version PREVIOUS_VERSION
Full Rollback

Revert code to previous version
Rollback database migrations
Restore configurations
Clear caches
Verify functionality

Post-Deployment
Verification Steps

 Health checks passing
 Metrics within normal range
 No error spikes in logs
 Key user flows working
 Database connections stable
 Cache hit rate normal

Communication
markdown**Deployment Complete**

Version: 1.2.0
Deployed: 2026-02-11 14:30 UTC
Duration: 15 minutes
Status: SUCCESS

Changes:
- Feature X enabled
- Bug fix for Y
- Performance improvements

Metrics:
- Response time: 150ms (target: 200ms)
- Error rate: 0.01% (target: <0.1%)
- CPU usage: 45% (normal)