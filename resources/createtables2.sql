DROP TABLE IF EXISTS Expense;
DROP TABLE IF EXISTS Budget;
DROP TABLE IF EXISTS Week;
DROP TABLE IF EXISTS Category;

CREATE TABLE Category (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE Budget (
    version INTEGER NOT NULL,
    category INTEGER NOT NULL,
    spend_limit FLOAT,
    date_from DATE NOT NULL,
    date_to DATE,
    PRIMARY KEY (version, category),
    FOREIGN KEY (category) REFERENCES Category(id)
);

CREATE TABLE Expense (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    amount FLOAT NOT NULL,
    category INTEGER NOT NULL,
    date DATE NOT NULL,
    description VARCHAR(255),
    recurring BOOL,
    FOREIGN KEY (category) REFERENCES Category(id)
);