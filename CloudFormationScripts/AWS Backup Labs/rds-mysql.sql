mysql -h <endpoint> -P 3306 -u <mymasteruser> -p

SHOW DATABASES;
CREATE DATABASE employees;
SHOW DATABASES;
USE employees;
CREATE TABLE employee_tbl (id INT NOT NULL AUTO_INCREMENT, first_name VARCHAR(255) NOT NULL, last_name VARCHAR(255), PRIMARY KEY (id));
SHOW TABLES;

INSERT INTO employee_tbl(first_name, last_name) VALUES ('John', 'Smith'), ('Andy', 'Jassy'), ('Charlie', 'Bell');
SELECT * FROM employee_tbl;

!-- Run backup

!-- Accidentally insert extra records
INSERT INTO employee_tbl(first_name, last_name) VALUES ('John', 'Smith'), ('Andy', 'Jassy'), ('Charlie', 'Bell');
SELECT * FROM employee_tbl;

!-- Run restore
exit;
mysql -h <newrdsendpoint> -P 3306 -u <mymasteruser> -p

SHOW DATABASES;
USE employees;
SHOW TABLES;
SELECT * FROM employee_tbl;