# **Raspberry Pi Project**
This project aims to replace the Control By Web (CBW) in the current systems with a custom circuit board with an embedded Raspberry Pi.
This repository is for the R&D code and built around the DPM (Dual-Purpose Modular) system.

_[Control By Web](https://controlbyweb.com/)_

## **Background**

- A CBW is able to control relays remotely, provide real time sensor reaadings and web interface that allows for remote relay control.
- The goal of this project is to create an embedded circuit board that can match the capabilities of a CBW.
- In addition to matching the base functionality of a CBW we aim to improve upon the design to fit the use case better.

## **Docker Installation**

To install Project Title, follow these steps:
1. Get Docker: **`curl -fsSL https://get.docker.com -o get-docker.sh`**
2. Install Docker: **`sudo sh get-docker.sh`**
3. Add 'pi' user to the 'docker' group: **`sudo usermod -aG docker pi`**
4. Install Docker Compose dependencies: **`sudo apt install -y libffi-dev libssl-dev python3 python3-pip`**
5. Install Docker Compose: **`sudo pip3 install docker-compose`**

## **Project Installation**

1. Clone the repository: **`git clone https://github.com/ValorenceCLE/RPi.git`**
2. Navigate to the project directory: **`cd RPi`**
3. Build the project: **`docker-compose build`**
4. Start the project: **`docker-compose up`**

## **Project Configuration**

1. Navigate to project directory: **`cd RPi`**
2. Create 'config' folder insider project directory: **`mkdir config`**
3. Navigate to config directory: **`cd config`**
4. The code expects three files to exist in this folder: *`auth.env`* , *`influxdb.env`* and *`nginx.conf`*  

        A) auth.env stores the credentials for the user groups: 'USER_USERNAME', 'USER_PASSWORD', 'ADMIN_USERNAME' and 'ADMIN_PASSWORD'
        B) influxdb.env stores the settings for InfluxDB to be set up automatically. See https://hub.docker.com/_/influxdb for details.
        C) nginx.conf stores the settings for NGINX to serve as a reverse proxy. See Nginx documentation for more info

## ***Optional Configuration***
### Setting Up daily reboots
**This must be done after the initial build. The services will not build the images.**
1. Navigate to project directory: **`cd RPi`**
2. Navigate to scripts directory: **`cd scripts`**
3. Show the files in the directory: **`ls`**
4. All of the .sh files need to be made exicutable: **`sudo chmod +x file_name`**
5. Create a cron job to run the 'shutdown.sh' script every night (Or any inerval)
6. There are two files in the scripts directory with the extension .service. These are templates for real systemd services
7. On the host machine create a two new services: **`sudo nano /etc/systemd/system/service_name.service`**
8. After creating both of the services using the templates reload the daemon: **`sudo systemctl daemon-reload`**
9. Enable both of the services: **`sudo systemctl enable service_name.service`**
10. Now the code will start automatically on boot as well as automatically shut down every night.


## **Acknowledgment**

All code was written and developed by **Landon Bell** an employee of **Valorence**.

All Hardware was developed by **Kelton Page** an employee of **Valorence**.  

