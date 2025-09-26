#!/usr/bin/bash

git pull origin deploy-to-rush-admin
systemctl --user restart python-deployer
