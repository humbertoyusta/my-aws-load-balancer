from flask import Flask, request, redirect
from threading import Thread
from time import sleep
import requests
import boto3

app = Flask(__name__)

# List of your backend servers
backends = []
healthy_backends = list(backends)

def service_discovery():
    global backends
    ec2 = boto3.client('ec2', region_name='eu-north-1')

    while True:
        response = ec2.describe_instances(
            Filters=[
                {
                    'Name': 'tag:your-tag-key',
                    'Values': ['your-tag-value']
                },
                {
                    'Name': 'instance-state-name',
                    'Values': ['running']
                }
            ]
        )

        backends = [
            f"http://{instance['PrivateIpAddress']}:8080"
            for reservation in response['Reservations']
            for instance in reservation['Instances']
        ]

        sleep(10)

def health_check():
    global healthy_backends
    while True:
        for backend in backends:
            try:
                response = requests.get(f'{backend}/health', timeout=2)
                if response.status_code == 200:
                    if backend not in healthy_backends:
                        healthy_backends.append(backend)
                else:
                    if backend in healthy_backends:
                        healthy_backends.remove(backend)
            except requests.exceptions.RequestException:
                if backend in healthy_backends:
                    healthy_backends.remove(backend)
        sleep(10)

@app.route('/')
def load_balancer():
    if not healthy_backends:
        return 'No healthy backends', 503
    # Round-robin load balancing by rotating the list of healthy backends
    backend = healthy_backends.pop(0)
    healthy_backends.append(backend)
    return redirect(backend, 302)


if __name__ == "__main__":
    # Start the service discovery and health check threads
    Thread(target=service_discovery).start()
    Thread(target=health_check).start()
    app.run(port=8080, host="0.0.0.0", debug=True)
