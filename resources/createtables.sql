DROP TABLE IF EXISTS Expense;
DROP TABLE IF EXISTS Budget;
DROP TABLE IF EXISTS Week;
DROP TABLE IF EXISTS Category;

CREATE TABLE Week (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    budget_version INTEGER NOT NULL
);

CREATE TABLE Category (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE Budget (
    version INTEGER NOT NULL,
    category INTEGER NOT NULL,
    spend_limit FLOAT,
    PRIMARY KEY (version, category),
    FOREIGN KEY (category) REFERENCES Category(id)
);

CREATE TABLE Expense (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    amount FLOAT NOT NULL,
    category INTEGER NOT NULL,
    date DATE NOT NULL,
    week INTEGER NOT NULL,
    description VARCHAR(255),
    FOREIGN KEY (category) REFERENCES Category(id),
    FOREIGN KEY (week) REFERENCES Week(id)
);