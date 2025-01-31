#!/bin/sh

pip install -r ../requirements.txt
chown ec2-user /cyber-dashboard-flask -R
cp flaskapp.service /etc/systemd/system/flaskapp.service
sudo systemctl start flaskapp
sudo systemctl enable flaskapp

sudo amazon-linux-extras install nginx1
cp nginx.conf /etc/nginx/conf.d/app.conf
sudo systemctl start nginx
sudo systemctl enable nginx