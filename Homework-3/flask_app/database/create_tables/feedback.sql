CREATE TABLE IF NOT EXISTS `feedback` (
`comment_id`     int(11)       NOT NULL AUTO_INCREMENT 	COMMENT 'The comment id',
`name`           varchar(100)  NOT NULL                	COMMENT 'The name of person leaving feedback',
`email`          varchar(100)  NOT NULL                	COMMENT 'email of person leaving feedback',
`comment`        TEXT          NOT NULL                	COMMENT 'comment left',
PRIMARY KEY  (`comment_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT="feedback that I have recieved on my work";