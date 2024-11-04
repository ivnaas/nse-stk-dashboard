#install docker
sudo yum update -y
sudo yum install docker -y
sudo systemctl start docker
sudo systemctl enable docker
docker --version

or

sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo chkconfig docker on

#install docker-compose
sudo curl -L https://github.com/docker/compose/releases/download/1.22.0/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose version

doc ref# https://gist.github.com/npearce/6f3c7826c7499587f00957fee62f8ee9

#docker compose execution
change to nse-stk-dashboard
docker-compose up -d

#build docker image
cd nse-stk-dashboard
docker build -t nse-dash .
docker images

#create service and start on reboot

vi /etc/systemd/system/dcompose.service
systemctl start dcompose
systectl status dcompose
systemctl enable dcompose

docker ps -a

#another option to setup cron
#install cron and start docker-compose on evrey reboot
sudo dnf install cronie -y
sudo systemctl enable crond
sudo systemctl start crond
crontab -e
@reboot cd /home/ec2-user/nse-stk-dashboard && docker-compose up -d
