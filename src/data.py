from datetime import timedelta
from json import load

import mysql.connector
from mysql.connector import Error
from app import Recurring


class DBConnection:
    def __init__(self, connection, cursor):
        self.connection = connection
        self.cursor = cursor

    def close(self):
        self.cursor.close()
        self.connection.close()

    def get_category(self, category):
        sql_category = """SELECT id FROM Category WHERE name=%s"""
        try:
            self.cursor.execute(sql_category, (category,))
            category_id = self.cursor.fetchone()[0]
            return category_id
        except Error as e:
            print("Error occurred while getting category: ", e)

    def get_categories(self):
        try:
            self.cursor.execute("SELECT name FROM Category")
            categories = self.cursor.fetchall()
            return categories
        except Error as e:
            print("Error occurred while getting categories: ", e)

    def add_expense(self, expense):
        try:
            sql_add = """INSERT INTO Expense (amount, category, date, description, recurring) VALUES (?, ?, ?, ?, ?)"""
            category_id = self.get_category(expense.category)
            details = (expense.amount, category_id, expense.date, expense.description, expense.recurring)
            self.cursor.execute(sql_add, details)
            self.connection.commit()
        except Error as e:
            print("Error occurred while adding expense: ", e)

    def get_budget(self):
        version = self.get_latest_budget_version()
        try:
            sql = """SELECT C.name AS category, B.spend_limit FROM Budget B INNER JOIN Category C ON B.category = C.id WHERE B.version = ?"""
            self.cursor.execute(sql, (version,))
            budget = self.cursor.fetchall()
            return budget
        except Error as e:
            print("Error occurred while getting expense: ", e)

    def add_new_budget(self, budget, date_from):
        old_version = self.get_latest_budget_version()
        date_to = date_from - timedelta(days=1)
        try:
            sql = """UPDATE Budget SET date_to = ? WHERE version = ?"""
            self.cursor.execute(sql, (date_to, old_version))
            self.connection.commit()

            for category, spend_limit in budget.items():
                self.add_category_budget(old_version+1, category, spend_limit, date_from, None)

        except Error as e:
            print("Error occurred while creating a new budget: ", e)

    def add_category_budget(self, version, category, spend_limit, date_from, date_to):
        try:
            sql = """INSERT INTO Budget (version, category, spend_limit, date_from, date_to) 
            SELECT ?, id, ?, ?, ? FROM Category WHERE name = ?"""
            details = (version, spend_limit, date_from, date_to, category)
            self.cursor.execute(sql, details)
            self.connection.commit()
        except Error as e:
            print("Error occurred while creating a new budget: ", e)

        return

    def get_latest_budget_version(self):
        try:
            sql = """SELECT MAX(version) FROM Budget """
            self.cursor.execute(sql)
            version = self.cursor.fetchone()[0]
            return version
        except Error as e:
            print("Error occurred while getting latest budget version: ", e)

    def get_spending(self, start, end):
        try:
            sql = """SELECT C.name AS category, SUM(E.amount) AS spending FROM Expense E INNER JOIN Category C ON E.category = C.id WHERE E.date >= ? AND E.date <= ? GROUP BY (C.name)"""
            dates = (start, end)
            self.cursor.execute(sql, dates)
            spending = self.cursor.fetchall()
            return spending
        except Error as e:
            print("Error occurred while getting spending: ", e)

    def get_recurring_payments(self):
        try:
            sql = """SELECT R.id AS id, R.name AS name, amount, C.name AS category, day_of_the_month FROM Recurring R INNER JOIN Category C on R.category = C.id WHERE active = TRUE"""
            self.cursor.execute(sql)
            output = self.cursor.fetchall()
            recurring_payments = []
            for row in output:
                payment = Recurring(row[0], row[1].decode(), row[2], row[3].decode(), row[4])
                recurring_payments.append(payment)

            return recurring_payments
        except Error as e:
            print("Error occurred while getting spending: ", e)


def connect():
    try:
        with open("db_config.json") as src_file:
            config = load(src_file)
            host = config["dbHost"]
            db_name = config["dbName"]
            user = config["dbUser"]
            password = config["dbPassword"]
        connection = mysql.connector.connect(host=host, database=db_name, user=user, passwd=password,
                                             auth_plugin="mysql_native_password")
        if connection.is_connected():
            cursor = connection.cursor(prepared=True)
            cursor.execute("select database();")
            record = cursor.fetchone()
            db = DBConnection(connection, cursor)
            return db
    except Error as e:
        print("Error while connecting to MySQL", e)
