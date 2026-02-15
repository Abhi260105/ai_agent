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