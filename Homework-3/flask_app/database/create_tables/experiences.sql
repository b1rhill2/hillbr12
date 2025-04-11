CREATE TABLE IF NOT EXISTS experiences (
experience_id     int(11)        NOT NULL AUTO_INCREMENT 	 COMMENT 'The experience id',
position_id       int(100)       NOT NULL                  COMMENT 'Organization Type; e.g. fastfood, retail, professional',
name              varchar(100)   NOT NULL                	 COMMENT 'The name of the organization',
description       TEXT           DEFAULT NULL            	 COMMENT 'description of experience',
hyperlink         varchar(2100)  DEFAULT NULL            	 COMMENT 'link to experience',
start_date        DATE  DEFAULT  NULL            	         COMMENT 'start date of experience',
end_date          DATE  DEFAULT  NULL            	         COMMENT 'end date of experience',
PRIMARY KEY  (experience_id),
FOREIGN KEY  (position_id)REFERENCES positions(position_id)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT="Experience That I've Dealt With";

