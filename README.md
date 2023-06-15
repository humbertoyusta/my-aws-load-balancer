# Flask Load Balancer

This is a simple Python-based load balancer made with Flask, intended for learning purposes. 

The load balancer works with AWS EC2 instances. It uses service discovery to identify all instances with a specific tag (in this case, 'flaskapp-group') and load balances across these instances using a round-robin strategy.

It is intended to run in an EC2 instance with some role that has some policy that allows to use describe_instances API call. 

The instances that are going to be load balanced should have a tag with the key 'Name' and the value 'flaskapp-group'. 

The instances should also have a security group that allows incoming traffic on port 8080.

## How it Works

1. The `service_discovery` function continuously checks the AWS EC2 instances that have the 'flaskapp-group' tag and are in the running state. This function updates the list of services every 10 seconds.

2. The `health_check` function continuously checks the health of the services discovered by the `service_discovery` function. If a service is found to be unhealthy (i.e., it does not respond to a '/health' request within 2 seconds or any other exception occurs during the request), it is removed from the list of healthy services. This function updates the list of healthy services every 10 seconds.

3. The `load_balancer` function handles all incoming requests to the load balancer. It redirects the incoming requests to one of the healthy backend services. If there are no healthy services, it responds with a 503 status code. The backend service to which the request is redirected is selected using a simple round-robin strategy. After redirecting a request, the selected service is moved to the end of the list of healthy services. All redirects are logged in the 'app.log' file. Responds with 307 instead of 302 to tell the client to preserve the request method and body.