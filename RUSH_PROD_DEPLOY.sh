#!/usr/bin/bash

git pull origin deploy-to-rush-admin
sudo systemctl restart python-deployer.service
