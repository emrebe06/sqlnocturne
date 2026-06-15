# SQLNocturne Kubernetes

Minimal local Kubernetes manifests for the SQLNocturne runtime.

```bash
docker build -t sqlnocturne:local .
kubectl apply -f deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/pvc.yaml
kubectl apply -f deploy/kubernetes/deployment.yaml
```

For PostgreSQL or MySQL in production, set `SQLNOCTURNE_DATABASE` to the network
URI and install the optional driver in your image.
