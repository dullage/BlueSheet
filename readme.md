# BlueSheet
A web app to help manage personal finances.

![Dashboard - Desktop](docs/dashboard-desktop.png)
![Outgoings - Mobile](docs/outgoings-mobile.png)

## Introduction
I was looking for a project to help me learn HTML and CSS and so I built this web app to replace a number of spreadsheets I was using to track my own personal finances.

It was designed with the following methodology in mind.

1. Salary is paid monthly and not used until the end of the month.
2. On the last day of the month, enough money to cover all monthly outgoings is paid into the account from which they are taken.
3. The remaining balance (expandable income) is saved and then withdrawn weekly (on the same day every week) throuhout the month.

## Other Feaures
* Salary Calculation (UK) - Calculate net salary and see tax, NI and pension breakdown.
* Record and save for Annual Expenses - Link a monthly outgoing to your annual expenses so that the money is saved and ready when needed.
* Starling Bank Integration - See your main acocunt and savings goal balances on the dashboard.
* Multiple User Support - Multiple users can each have their own password protected set of data.
* Mobile Responsive.

## Installation
This is a flask python app so can be deployed in [a number of different ways](http://flask.pocoo.org/docs/1.0/deploying/).

The easiest way I have found is to run the app in a Docker container using tiangolo's great [uwsgi-nginx-flask image](https://hub.docker.com/r/tiangolo/uwsgi-nginx-flask). docker-compose can also be used to help things.

Linux Steps:
```shell
# Create an installation directory
mkdir BlueSheet
cd BlueSheet

# Clone the repo
git clone https://github.com/Dullage/BlueSheet.git

# Create a docker and docker-compose file
touch docker
touch docker-compose.yaml
```
You should now have an installation directory that looks like this:
* **BlueSheet**
    * docker
    * docker-compose.yaml
    * **BlueSheet**
        * **static**
        * **templates**
        * .gitattributes
        * ...

Next open the docker and docker-compose files for editing and add the following (changing variables where necessary).

```dockerfile
# dockerfile
FROM tiangolo/uwsgi-nginx-flask:python3.6

COPY ./BlueSheet /app

RUN pip install -r /app/requirements.txt
```
```yaml
# docker-compose.yaml
version: '3'
services:
  bluesheet:
    build: .
    image: bluesheet
    container_name: "bluesheet"
    # Keep the database outside the container
    volumes:
      - "./BlueSheet.db:/app_data/BlueSheet.db"
    # Tell BlueSheet where to find the database
    environment:
      - DATABASE_PATH=/app_data/BlueSheet.db
    # Run on local port 5000
    ports:
      - 5000:80
    restart: "always"
```
Once created you should just be able to run:
```shell
docker-compose up -d
```