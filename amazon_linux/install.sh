#!/bin/sh

pip install -r ../requirements.txt
chown ec2-user /cyber-dashboard-flask -R
cp flaskapp.service /etc/systemd/system/flaskapp.service
sudo systemctl start flaskapp
sudo systemctl enable flaskapp
