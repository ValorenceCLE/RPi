# Raspberry Pi Project
This project aims to replace the Control By Web (CBW) in the current systems with a custom circuit board with an embedded Raspberry Pi.

## Background:
#### - A CBW is able to control relays remotely, provide real time sensor reaadings and web interface that allows for remote relay control.
#### - The goal of this project is to create an embedded circuit board that can match the capabilities of a CBW.
#### - In addition to matching the base functionality of a CBW we aim to imrpove upon the design to fit the use case better.
## Key Features:
#### - Adding additional sensors that allowed for better environmental insights, insights into power consumption from the router and camera as well as gathering cellular data to provide insights into signal quality.
#### - Adding on board SSD storage, this allowed the raspberry pi to be set up as a NAS for the camera.
#### - Setting up the raspberry pi as a Syslog server, this was done to be able to analyze syslogs to gain insights into issues.
#### - Building a more detailed tech support dashboard that will enable more detailed and informed troubleshooting.
#### - Run analysis on all of the data being gathered and use it to create a real time alerting system. By detecting anomalies in the data or syslogs we aim to be able to alert both the client and our tech support team of the issue to allow them to either fix it preemptively or quickly resolve any downtime.
#### - Build out a database on each raspberry pi to store all gathered data to be able to detect historical trends and visualize data.
#### - Develope real time data driven alerting to be able to respond to problems as they arrive
#### - Proactive error handling and event driven actions. The goal is to use the data being collected to detect possible issues and take actions to automatically fix them before they become an issue.
## Installation:
