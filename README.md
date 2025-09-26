# Python-Deployer
Python-Deployer is a Flask app that listens for deployment webhooks and runs the corresponding deploy script on the server if the request is authenticated.

### How to Run
Use `poetry run python main.py` for development and `poetry run python production.py` to run a gunicorn server for your production environment. See the `config.yaml` file for details.

### How to simulate a deployment locally
You may want to simulate a deployment for development purposes. The easiest way to do this is to run `chmod +x test_deploy_endpoint.sh`, `chmod +x test_trigger_deploy.sh`, and then run `./test_trigger_deploy.sh`.
