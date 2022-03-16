import mysql.connector
from mysql.connector import Error
from json import load


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
        try:
            sql = """SELECT C.name AS category, B.spend_limit FROM Budget B INNER JOIN Category C ON B.category = C.id"""
            self.cursor.execute(sql)
            budget = self.cursor.fetchall()
            return budget
        except Error as e:
            print("Error occurred while getting expense: ", e)

    def get_spending(self, start, end):
        try:
            sql = """SELECT C.name AS category, SUM(E.amount) AS spending FROM Expense E INNER JOIN Category C ON E.category = C.id WHERE E.date >= ? AND E.date <= ? GROUP BY (C.name)"""
            dates = (start, end)
            self.cursor.execute(sql, dates)
            spending = self.cursor.fetchall()
            return spending
        except Error as e:
            print("Error occurred while getting spending: ", e)


def connect():
    try:
        with open("config.json") as src_file:
            config = load(src_file)
            host = config["dbHost"]
            db_name = config["dbName"]
            user = config["dbUser"]
        connection = mysql.connector.connect(host=host, database=db_name, user=user)
        if connection.is_connected():
            cursor = connection.cursor(prepared=True)
            cursor.execute("select database();")
            record = cursor.fetchone()
            db = DBConnection(connection, cursor)
            return db
    except Error as e:
        print("Error while connecting to MySQL", e)
