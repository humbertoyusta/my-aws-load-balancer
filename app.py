from flask import Flask, request, redirect
from threading import Thread
from time import sleep
import requests
import boto3

app = Flask(__name__)

# List of your backend servers
services = []
healthy_services = list(services)

def service_discovery():
    global services
    ec2 = boto3.client('ec2', region_name='eu-north-1')

    while True:
        response = ec2.describe_instances(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': ['flaskapp-group']
                },
                {
                    'Name': 'instance-state-name',
                    'Values': ['running']
                }
            ]
        )

        services = [
            f"http://{instance['PublicIpAddress']}:8080"
            for reservation in response['Reservations']
            for instance in reservation['Instances']
        ]

        sleep(10)

def health_check():
    global healthy_services
    while True:
        for service in services:
            try:
                response = requests.get(f'{service}/health', timeout=2)
                if response.status_code == 200:
                    if service not in healthy_services:
                        healthy_services.append(service)
                else:
                    if service in healthy_services:
                        healthy_services.remove(service)
            except requests.exceptions.RequestException:
                if service in healthy_services:
                    healthy_services.remove(service)
        sleep(10)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def load_balancer(path):
    if not healthy_services:
        return 'No healthy backends', 503
    # Round-robin load balancing by rotating the list of healthy backends
    service = healthy_services.pop(0)
    healthy_services.append(service)
    # log the backend we are sending traffic to and send to a file app.log
    with open('app.log', 'a') as f:
        f.write(f'Sending traffic to {service}/{path}\n')
    return redirect(f'{service}/{path}', 302)


if __name__ == "__main__":
    # Start the service discovery and health check threads
    Thread(target=service_discovery).start()
    Thread(target=health_check).start()
    app.run(port=8080, host="0.0.0.0", debug=True)
