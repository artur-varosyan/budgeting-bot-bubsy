import mysql.connector
from mysql.connector import Error


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
            sql_add = """INSERT INTO Expense (amount, category, date, week, description) VALUES (?, ?, ?, ?, ?)"""
            category_id = self.get_category(expense.category)
            details = (expense.amount, category_id, expense.date, expense.week, expense.description)
            self.cursor.execute(sql_add, details)
            self.connection.commit()
        except Error as e:
            print("Error occurred while adding expense: ", e)


def connect():
    try:
        connection = mysql.connector.connect(host='localhost', database='budgetingbot_test', user='budgeting_bot')
        if connection.is_connected():
            cursor = connection.cursor(prepared=True)
            cursor.execute("select database();")
            record = cursor.fetchone()
            db = DBConnection(connection, cursor)
            return db
    except Error as e:
        print("Error while connecting to MySQL", e)
