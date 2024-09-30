# Raspberry Pi Project

### This project aims to replace the Control By Web (CBW) in the current systems with a Raspberry Pi to allow for more computing options in our product offerings.

# Background:
#### The CBW was able to control relays remotely, provide real time sensor reaadings (temperature, voltage) and the CBW provided a publicly accessible web interface with user authentication to control the relays remotely.
#### Being able to match the functionality of the CBW and all of its features was the first objective of this project.
#### However, in addition to the base functionality of the CBW we decided to improve and make a better system to control/monitor systems remotely.
# To improve upon the CBW we have added additional functionality to the system by:
#### - Adding additional sensors that allowed for better environmental insights, insights into power consumption from the router and camera as well as gathering cellular data to provide insights into signal quality.
#### - Adding on board SSD storage, this allowed the raspberry pi to be set up as a NAS for the camera.
#### - Setting up the raspberry pi as a Syslog server, this was done to be able to analyze syslogs to gain insights into issues.
#### - Building a more detailed tech support dashboard that will enable more detailed and informed troubleshooting.
#### - Run analysis on all of the data being gathered and use it to create a real time alerting system. By detecting anomalies in the data or syslogs we aim to be able to alert both the client and our tech support team of the issue to allow them to either fix it preemptively or quickly resolve any downtime.
#### - Build out a database on each raspberry pi to store all gathered data to be able to detect historical trends and visualize data.
#### - Develope real time data driven alerting to be able to respond to problems as they arrive
#### - Proactive error handling and event driven actions. The goal is to use the data being collected to detect possible issues and take actions to automatically fix them before they become an issue.