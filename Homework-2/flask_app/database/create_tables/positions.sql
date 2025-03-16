LOAD DATA LOCAL INFILE 'flask_app/database/initial_data/positions.csv'
INTO TABLE positions
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(position_id, inst_id, title, responsibilities, start_date, end_date)
SET end_date = NULLIF(end_date, '');