CREATE TABLE IF NOT EXISTS `event_participants`(
`id`         int AUTO_INCREMENT PRIMARY KEY COMMENT 'this is the id of the list of participants',
`event_id`   INT          NOT NULL COMMENT 'this is the id of the associated event that participants are linked up to',
`user_email` VARCHAR(100) NOT NULL COMMENT 'this is the user email that are participating',
FOREIGN KEY (`event_id`) REFERENCES events(`event_id`)
)ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='Maps users to events they can join.';

select * from event_participants;