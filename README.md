## A Simple Notes app for the Cloud application Development Module: Group project

### Table of Contents

- [Prerequisites](#prerequisites)
- [Setup and Run Locally](#setup-and-run-locally)
- [Troubleshooting](#troubleshooting)

### Prerequisites

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/get-started)
- [Minikube](https://minikube.sigs.k8s.io/docs/)
- [Kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)

### Setup and run locally

1. Clone the repository to your local machine:

```bash
git clone https://github.com/Chamal1120/flask-notes-app.git
cd flask-notes-app
```

2. Start Minikube If not running yet:
```bash
minikube start
```

3. Get the Minikube IP (which you'll use to access the app):

```bash
minikube ip
```

4. Apply the deployment.yml file that contains the app's Kubernetes configuration:

```bash
kubectl apply -f deployment.yml
```

This will create a Deployment with 3 replicas and a NodePort service for external access:

5. Check if the pods and services are running correctly:

```bash
kubectl get pods
kubectl get svc flask-notes-service
```

6. Open a seperate terminal window and start Minikube tunnel to expose the service to your local machine (you should keep this running until you finish working with the app):

```bash
minikube tunnel
```

This command will set up a network route from your machine to the Kubernetes cluster.

7. Once the tunnel is established, open your browser and navigate to:

```
http://<minikube-ip>:31009
```

Replace <minikube-ip> with the IP you got from the minikube ip command.
You should now see the Flask Notes app running locally.

### Troubleshooting

1. "Connection Refused" Error: If you're unable to access the app, ensure that Minikube is running, the tunnel is up, and the correct IP is being used. You can check the service by running:

```bash
kubectl get svc flask-notes-service
```

2. Pods Not Running: If your pods are not starting or are stuck in a crash loop, check the logs for errors:

```bash
kubectl logs <pod-name>
```

3. Minikube Tunnel Issues: If the tunnel is not working, try restarting Minikube:

```bash
minikube stop
minikube start
minikube tunnel
```
