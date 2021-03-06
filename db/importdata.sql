LOAD DATA LOCAL INFILE 'categories.csv' 
INTO TABLE Category
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'budget.csv'
INTO TABLE Budget
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'expenses.csv'
INTO TABLE Expense
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n';