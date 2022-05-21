# Budgeting Bot Bubsy

### A personal finance budget-managing tool deployed as a chatbot on the messaging platform Telegram. Bubsy records your expenses, shows your spending and keeps track of your budget.

## Table of Contents
1. [About](#budgeting-bot-bubsy)
2. [Getting Started](#getting-started)
   * [Pre-requisites]()
   * [Configuration]()
3. [Usage](#usage)
4. [Deployment](#deployment)
5. [Future Improvements](#future-improvements)

# Getting Started

## Pre-Requisites
To run the application you will need the following:
* **Python 3.9+**
* SQL Relational Database

<br>

To install Python pre-requisites:
```
pip install -r requirements.txt
```
<br>

Note: To communicate with the bot via the messaging platform Telegram you need [Telegram](https://telegram.org/) account and application.

## Configuration
The application contains two configuration files you must fill in before running the bot:

* **src/db_config.json** <br>
  The configuration settings for the database.
  ```json
  {
  "dbHost": "localhost",
  "dbName": "budget",
  "dbUser": "bubsy"
  }
  ```
  
* **src/telegram_config.json** <br>
  _(Optionally) The configuration settings for the Telegram bot._
  ```json
  {
    "token": "token",
    "privateBot": true,
    "chatId": 0
  }
  ```

# Usage

You may run the application by: <br>
* `python app.py --terminal` to converse with the bot in the terminal, or alternatively, <br>
* `python app.py --telegram` (default) to use the messaging platform Telegram


# Deployment
The application has been deployed on an EC2 AWS instance.

# Future Improvements
Some of the features I plan to add to the project:
* Support for keeping track of recurring payments
* Showing a spending graph via Google Sheets API

To see an up-to-date list of features I am currently working on, see the [issues section]() of the repository.
