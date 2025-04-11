CREATE TABLE IF NOT EXISTS `skills` (
`skill_id`        int(11)       NOT NULL AUTO_INCREMENT 	COMMENT 'the skills id',
`experience_id`   int(100)      NOT NULL                    COMMENT 'Organization Type; e.g. fastfood, retail, professional',
`name`            varchar(100)  NOT NULL                	COMMENT 'The name of the skill',
`skill_level`     varchar(100)  DEFAULT NULL            	COMMENT ' current skill level: e.g. beginner, intermidate, master',
PRIMARY KEY  (`skill_id`),
FOREIGN KEY  (`experience_id`)REFERENCES experiences(experience_id)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT="Skills I Have";