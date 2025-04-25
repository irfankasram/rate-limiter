Rate Limiter

Guide to deploy, test, and validate each functionality of rate limiter service on a local Kubernetes cluster (using Docker Desktop).

For this particular deployment using Docker Desktop and local Kubernetes cluster:

Clone the GitHub repository:

1) Build the Docker image

docker build -t rate-limiter:latest .


2) Create Kubernetes Deployment and Service

kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

3) Configure endpoint

curl -Uri "http://localhost:{service_port_number}/configure" -Method POST -Body '{"endpoint":"test","requests_per_sec":1}' -ContentType "application/json"


4) Test Rate Limit

curl http://localhost:{service_port_number}/test
