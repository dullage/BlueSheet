# BlueSheet
A web app to help manage personal finances.

![Dashboard - Desktop](docs/dashboard-desktop.png)
![Outgoings - Mobile](docs/outgoings-mobile.png)

## Introduction
I was looking for a project to improve my (non-existent) HTML and CSS knowledge and so I built this web app to replace a number of spreadsheets I was using to track my own personal finances. It also gave me an opportunity to expolore SQL Alchemy and Jinja templating.

It was designed with the following methodology in mind.

1. Salary is paid monthly and not used until the end of the month.
2. On the last day of the month, enough money to cover all monthly outgoings is paid into the account from which they are taken.
3. The remaining balance (expandable income) is saved and then withdrawn weekly (on the same day every week) throuhout the month.

## Feaures
* Track monthly outgoings and ensure enough money is saved to cover them all.
* Record and save for Annual Expenses - Link a monthly outgoing to your annual expenses so that the money is saved and ready when needed.
* Record savings accounts and pensions to get a total of all savings.
* Link an outgoing to a saving to increase the savings account balance by that amount each month.
* Create "self loans" allowing you to borrow from savings and create a re-payment plan.
* Salary Calculation (UK) - Calculate net salary and see tax, NI and pension breakdown.
* Starling Bank Integration - See your main acocunt and savings goal balances on the dashboard.
* Multiple User Support - Multiple users can each have their own password protected set of data.
* Mobile Responsive.

## Change Log
24/02/2019
* Fixed session expiry.

14/03/2019
* Fixed an issue loading existing Weekly Pay Day config.
* Sensitive data is now stored as encrypted binary (see below).

## Data Encryption
The following data is stored as encrypted binary. The key to decrypt the data is generated on the server using the user password but is stored locally to the user in a cookie (and not on the server). Equally the password is not stored on the server either (only an irreversable hash). 

Barring a man-in-the-middle attack, only the end user will ever be able to see this data.

* Account: Names
* Account: Notes
* Configuration: Annual Gross Salary
* Configuration: Annual Tax Allowance
* Configuration: Tax Rate
* Configuration: Annual NI Allowance
* Configuration: NI Rate
* Configuration: Annual Non Pensionable Value
* Configuration: Pension Contribution
* Configuration: Weekly Spending Amount
* Configuration: Starling API Key
* Monthly Outgoing: Names
* Monthly Outgoing: Values
* Monthly Outgoing: Notes
* Annual Expense: Names
* Annual Expense: Values
* Annual Expense: Notes
* Savings: Names
* Savings: Balance
* Savings: Notes

## Installation
This is a flask python app so can be deployed in [a number of different ways](http://flask.pocoo.org/docs/1.0/deploying/). I personally run this in a [Docker](https://www.docker.com/) container using [Gunicorn](https://gunicorn.org/). This is then served by [Caddy Web Server](https://caddyserver.com/).

# Creating a user account
bluesheet.py is a command line tool allowing you to add and unlock user accounts. Usage:
```shell
python /path/to/bluesheet.py add-user -u joe.bloggs@example.com -p MyS3curePwd!
```

When the user first logs in they will be taken to the configuration page.

# Unlokcing a user account
If a user enters an incorrect password more than 3 times in a row their account will be locked, to unlock an account you can run the following:
```shell
python /path/to/bluesheet.py unlock-user -u joe.bloggs@example.com
```