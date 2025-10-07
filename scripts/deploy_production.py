#!/usr/bin/env python3
"""
Project Singularity Production Deployment System
Advanced deployment orchestration with Docker, Kubernetes, and cloud integration
"""

import os
import sys
import json
import yaml
import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
from dataclasses import dataclass, asdict
import time
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    environment: str  # dev, staging, production
    cloud_provider: str  # aws, gcp, azure, local
    kubernetes_cluster: str
    docker_registry: str
    domain: str
    ssl_enabled: bool = True
    auto_scaling: bool = True
    monitoring_enabled: bool = True
    backup_enabled: bool = True

class ProjectSingularityDeployer:
    """
    Advanced deployment system for Project Singularity
    """
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.project_root = Path(__file__).parent.parent
        self.deployment_dir = self.project_root / "deployments"
        self.deployment_dir.mkdir(exist_ok=True)
        
        # Docker images
        self.images = {
            "api": f"{config.docker_registry}/singularity-api",
            "frontend": f"{config.docker_registry}/singularity-frontend",
            "worker": f"{config.docker_registry}/singularity-worker",
            "nginx": f"{config.docker_registry}/singularity-nginx"
        }
        
        # Version tag
        self.version = self._get_version()
    
    async def deploy_complete_system(self) -> Dict[str, Any]:
        """
        Deploy the complete Project Singularity system
        """
        try:
            logger.info(f"🚀 Starting deployment to {self.config.environment}")
            
            deployment_steps = [
                ("Building Docker images", self._build_docker_images),
                ("Pushing images to registry", self._push_docker_images),
                ("Generating Kubernetes manifests", self._generate_k8s_manifests),
                ("Deploying to Kubernetes", self._deploy_to_kubernetes),
                ("Setting up ingress and SSL", self._setup_ingress),
                ("Configuring monitoring", self._setup_monitoring),
                ("Running health checks", self._run_health_checks),
                ("Setting up auto-scaling", self._setup_auto_scaling)
            ]
            
            results = {}
            
            for step_name, step_func in deployment_steps:
                logger.info(f"📋 {step_name}...")
                start_time = time.time()
                
                try:
                    result = await step_func()
                    duration = time.time() - start_time
                    
                    results[step_name] = {
                        "success": True,
                        "duration": duration,
                        "result": result
                    }
                    
                    logger.info(f"✅ {step_name} completed in {duration:.2f}s")
                    
                except Exception as e:
                    logger.error(f"❌ {step_name} failed: {e}")
                    results[step_name] = {
                        "success": False,
                        "error": str(e)
                    }
                    
                    if self.config.environment == "production":
                        # Rollback on production failure
                        await self._rollback_deployment()
                        raise
            
            # Generate deployment summary
            summary = await self._generate_deployment_summary(results)
            
            logger.info("🎉 Deployment completed successfully!")
            return summary
            
        except Exception as e:
            logger.error(f"💥 Deployment failed: {e}")
            raise
    
    async def _build_docker_images(self) -> Dict[str, str]:
        """
        Build all Docker images for the system
        """
        built_images = {}
        
        # API Docker image
        api_dockerfile = self._generate_api_dockerfile()
        api_image = await self._build_docker_image("api", api_dockerfile)
        built_images["api"] = api_image
        
        # Frontend Docker image
        frontend_dockerfile = self._generate_frontend_dockerfile()
        frontend_image = await self._build_docker_image("frontend", frontend_dockerfile)
        built_images["frontend"] = frontend_image
        
        # Worker Docker image (for background APK building)
        worker_dockerfile = self._generate_worker_dockerfile()
        worker_image = await self._build_docker_image("worker", worker_dockerfile)
        built_images["worker"] = worker_image
        
        # Nginx reverse proxy
        nginx_dockerfile = self._generate_nginx_dockerfile()
        nginx_image = await self._build_docker_image("nginx", nginx_dockerfile)
        built_images["nginx"] = nginx_image
        
        return built_images
    
    def _generate_api_dockerfile(self) -> str:
        """Generate Dockerfile for the API service"""
        return f'''
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    git \\
    openjdk-17-jdk \\
    nodejs \\
    npm \\
    && rm -rf /var/lib/apt/lists/*

# Install Android SDK
ENV ANDROID_HOME=/opt/android-sdk
ENV PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

RUN mkdir -p $ANDROID_HOME && \\
    cd $ANDROID_HOME && \\
    curl -o sdk-tools.zip https://dl.google.com/android/repository/commandlinetools-linux-8512546_latest.zip && \\
    unzip sdk-tools.zip && \\
    rm sdk-tools.zip

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 singularity && \\
    chown -R singularity:singularity /app
USER singularity

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
    
    def _generate_frontend_dockerfile(self) -> str:
        """Generate Dockerfile for the frontend service"""
        return '''
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./
RUN npm ci --only=production

# Copy source code and build
COPY frontend/ .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY deployments/nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
'''
    
    def _generate_worker_dockerfile(self) -> str:
        """Generate Dockerfile for the worker service"""
        return '''
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for APK building
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    git \\
    openjdk-17-jdk \\
    nodejs \\
    npm \\
    gradle \\
    && rm -rf /var/lib/apt/lists/*

# Install Android SDK and build tools
ENV ANDROID_HOME=/opt/android-sdk
ENV PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin

RUN mkdir -p $ANDROID_HOME/cmdline-tools && \\
    cd $ANDROID_HOME/cmdline-tools && \\
    curl -o tools.zip https://dl.google.com/android/repository/commandlinetools-linux-8512546_latest.zip && \\
    unzip tools.zip && \\
    mv cmdline-tools latest && \\
    rm tools.zip

# Accept Android licenses
RUN yes | sdkmanager --licenses

# Install required SDK components
RUN sdkmanager "platform-tools" "platforms;android-33" "build-tools;33.0.0"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 worker && \\
    chown -R worker:worker /app
USER worker

# Start worker
CMD ["python", "-m", "celery", "worker", "-A", "core.worker", "--loglevel=info"]
'''
    
    def _generate_nginx_dockerfile(self) -> str:
        """Generate Dockerfile for nginx reverse proxy"""
        return '''
FROM nginx:alpine

# Copy nginx configuration
COPY deployments/nginx.conf /etc/nginx/nginx.conf
COPY deployments/ssl/ /etc/nginx/ssl/

# Create log directory
RUN mkdir -p /var/log/nginx

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
'''
    
    async def _build_docker_image(self, service: str, dockerfile_content: str) -> str:
        """
        Build a Docker image for a specific service
        """
        image_tag = f"{self.images[service]}:{self.version}"
        
        # Create temporary dockerfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.Dockerfile', delete=False) as f:
            f.write(dockerfile_content)
            dockerfile_path = f.name
        
        try:
            # Build image
            cmd = [
                "docker", "build",
                "-f", dockerfile_path,
                "-t", image_tag,
                str(self.project_root)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Docker build failed: {stderr.decode()}")
            
            logger.info(f"✅ Built image: {image_tag}")
            return image_tag
            
        finally:
            os.unlink(dockerfile_path)
    
    async def _push_docker_images(self) -> Dict[str, str]:
        """
        Push Docker images to registry
        """
        pushed_images = {}
        
        for service, base_image in self.images.items():
            image_tag = f"{base_image}:{self.version}"
            
            cmd = ["docker", "push", image_tag]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Docker push failed for {service}: {stderr.decode()}")
            
            pushed_images[service] = image_tag
            logger.info(f"✅ Pushed image: {image_tag}")
        
        return pushed_images
    
    async def _generate_k8s_manifests(self) -> Dict[str, str]:
        """
        Generate Kubernetes deployment manifests
        """
        manifests = {}
        
        # Namespace
        manifests["namespace"] = self._generate_namespace_manifest()
        
        # ConfigMaps and Secrets
        manifests["configmap"] = self._generate_configmap_manifest()
        manifests["secrets"] = self._generate_secrets_manifest()
        
        # Deployments
        manifests["api-deployment"] = self._generate_api_deployment()
        manifests["frontend-deployment"] = self._generate_frontend_deployment()
        manifests["worker-deployment"] = self._generate_worker_deployment()
        
        # Services
        manifests["api-service"] = self._generate_api_service()
        manifests["frontend-service"] = self._generate_frontend_service()
        
        # Ingress
        manifests["ingress"] = self._generate_ingress_manifest()
        
        # Persistent Volumes
        manifests["storage"] = self._generate_storage_manifest()
        
        # Write manifests to files
        manifest_files = {}
        for name, content in manifests.items():
            file_path = self.deployment_dir / f"{name}.yaml"
            with open(file_path, 'w') as f:
                f.write(content)
            manifest_files[name] = str(file_path)
        
        return manifest_files
    
    def _generate_namespace_manifest(self) -> str:
        """Generate namespace manifest"""
        return f'''
apiVersion: v1
kind: Namespace
metadata:
  name: singularity-{self.config.environment}
  labels:
    app: project-singularity
    environment: {self.config.environment}
'''
    
    def _generate_api_deployment(self) -> str:
        """Generate API deployment manifest"""
        return f'''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: singularity-api
  namespace: singularity-{self.config.environment}
  labels:
    app: singularity-api
    version: {self.version}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: singularity-api
  template:
    metadata:
      labels:
        app: singularity-api
        version: {self.version}
    spec:
      containers:
      - name: api
        image: {self.images["api"]}:{self.version}
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: {self.config.environment}
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: singularity-secrets
              key: openai-api-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: singularity-secrets
              key: database-url
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
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: apk-storage
          mountPath: /app/builds
      volumes:
      - name: apk-storage
        persistentVolumeClaim:
          claimName: singularity-storage
---
apiVersion: v1
kind: Service
metadata:
  name: singularity-api-service
  namespace: singularity-{self.config.environment}
spec:
  selector:
    app: singularity-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
'''
    
    def _generate_frontend_deployment(self) -> str:
        """Generate frontend deployment manifest"""
        return f'''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: singularity-frontend
  namespace: singularity-{self.config.environment}
  labels:
    app: singularity-frontend
    version: {self.version}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: singularity-frontend
  template:
    metadata:
      labels:
        app: singularity-frontend
        version: {self.version}
    spec:
      containers:
      - name: frontend
        image: {self.images["frontend"]}:{self.version}
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: singularity-frontend-service
  namespace: singularity-{self.config.environment}
spec:
  selector:
    app: singularity-frontend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: ClusterIP
'''
    
    def _generate_ingress_manifest(self) -> str:
        """Generate ingress manifest"""
        tls_config = ""
        if self.config.ssl_enabled:
            tls_config = f'''
  tls:
  - hosts:
    - {self.config.domain}
    secretName: singularity-tls
'''
        
        return f'''
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: singularity-ingress
  namespace: singularity-{self.config.environment}
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:{tls_config}
  rules:
  - host: {self.config.domain}
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: singularity-api-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: singularity-frontend-service
            port:
              number: 80
'''
    
    async def _deploy_to_kubernetes(self) -> Dict[str, Any]:
        """
        Deploy manifests to Kubernetes cluster
        """
        deployment_results = {}
        
        # Apply manifests in order
        manifest_order = [
            "namespace",
            "secrets",
            "configmap",
            "storage",
            "api-deployment",
            "frontend-deployment",
            "worker-deployment",
            "ingress"
        ]
        
        for manifest_name in manifest_order:
            manifest_file = self.deployment_dir / f"{manifest_name}.yaml"
            
            if manifest_file.exists():
                cmd = ["kubectl", "apply", "-f", str(manifest_file)]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"Kubectl apply failed for {manifest_name}: {stderr.decode()}")
                
                deployment_results[manifest_name] = {
                    "status": "applied",
                    "output": stdout.decode()
                }
                
                logger.info(f"✅ Applied {manifest_name}")
        
        # Wait for deployments to be ready
        await self._wait_for_deployments()
        
        return deployment_results
    
    async def _wait_for_deployments(self):
        """
        Wait for all deployments to be ready
        """
        deployments = ["singularity-api", "singularity-frontend", "singularity-worker"]
        namespace = f"singularity-{self.config.environment}"
        
        for deployment in deployments:
            cmd = [
                "kubectl", "rollout", "status",
                f"deployment/{deployment}",
                "-n", namespace,
                "--timeout=300s"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Deployment {deployment} failed to become ready: {stderr.decode()}")
            
            logger.info(f"✅ Deployment {deployment} is ready")
    
    async def _setup_monitoring(self) -> Dict[str, Any]:
        """
        Set up monitoring and observability
        """
        if not self.config.monitoring_enabled:
            return {"status": "disabled"}
        
        monitoring_components = {}
        
        # Prometheus monitoring
        prometheus_manifest = self._generate_prometheus_manifest()
        monitoring_components["prometheus"] = await self._apply_manifest("prometheus", prometheus_manifest)
        
        # Grafana dashboards
        grafana_manifest = self._generate_grafana_manifest()
        monitoring_components["grafana"] = await self._apply_manifest("grafana", grafana_manifest)
        
        # Alert manager
        alertmanager_manifest = self._generate_alertmanager_manifest()
        monitoring_components["alertmanager"] = await self._apply_manifest("alertmanager", alertmanager_manifest)
        
        return monitoring_components
    
    async def _run_health_checks(self) -> Dict[str, Any]:
        """
        Run comprehensive health checks
        """
        health_results = {}
        
        # API health check
        api_health = await self._check_api_health()
        health_results["api"] = api_health
        
        # Frontend health check
        frontend_health = await self._check_frontend_health()
        health_results["frontend"] = frontend_health
        
        # Database connectivity
        db_health = await self._check_database_health()
        health_results["database"] = db_health
        
        # External services
        external_health = await self._check_external_services()
        health_results["external_services"] = external_health
        
        return health_results
    
    async def _check_api_health(self) -> Dict[str, Any]:
        """Check API health"""
        try:
            url = f"https://{self.config.domain}/api/health"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return {"status": "healthy", "response_time": response.elapsed.total_seconds()}
            else:
                return {"status": "unhealthy", "status_code": response.status_code}
        
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_version(self) -> str:
        """Get current version from git or timestamp"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
        
        except Exception:
            pass
        
        # Fallback to timestamp
        return f"v{int(time.time())}"
    
    async def _generate_deployment_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate deployment summary report
        """
        successful_steps = sum(1 for result in results.values() if result.get("success", False))
        total_steps = len(results)
        
        summary = {
            "deployment_id": f"deploy-{self.version}-{int(time.time())}",
            "environment": self.config.environment,
            "version": self.version,
            "timestamp": time.time(),
            "success_rate": successful_steps / total_steps,
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": total_steps - successful_steps,
            "endpoints": {
                "frontend": f"https://{self.config.domain}",
                "api": f"https://{self.config.domain}/api",
                "docs": f"https://{self.config.domain}/api/docs"
            },
            "steps": results
        }
        
        # Save summary to file
        summary_file = self.deployment_dir / f"deployment-summary-{self.version}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary

async def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy Project Singularity")
    parser.add_argument("--environment", choices=["dev", "staging", "production"], required=True)
    parser.add_argument("--cloud-provider", choices=["aws", "gcp", "azure", "local"], default="aws")
    parser.add_argument("--cluster", required=True, help="Kubernetes cluster name")
    parser.add_argument("--registry", required=True, help="Docker registry URL")
    parser.add_argument("--domain", required=True, help="Domain name for the application")
    parser.add_argument("--no-ssl", action="store_true", help="Disable SSL")
    parser.add_argument("--no-monitoring", action="store_true", help="Disable monitoring")
    
    args = parser.parse_args()
    
    # Create deployment configuration
    config = DeploymentConfig(
        environment=args.environment,
        cloud_provider=args.cloud_provider,
        kubernetes_cluster=args.cluster,
        docker_registry=args.registry,
        domain=args.domain,
        ssl_enabled=not args.no_ssl,
        monitoring_enabled=not args.no_monitoring
    )
    
    # Initialize deployer
    deployer = ProjectSingularityDeployer(config)
    
    try:
        # Run deployment
        summary = await deployer.deploy_complete_system()
        
        print("\n🎉 Deployment Summary:")
        print(f"Environment: {summary['environment']}")
        print(f"Version: {summary['version']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Frontend URL: {summary['endpoints']['frontend']}")
        print(f"API URL: {summary['endpoints']['api']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"💥 Deployment failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
