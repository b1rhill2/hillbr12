CREATE TABLE IF NOT EXISTS `events` (
`event_id`         int(11) NOT NULL auto_increment PRIMARY KEY        COMMENT 'the id of this event',
`event_name`       varchar(100) NOT NULL                    COMMENT 'the role of the event name',
`start_date`        DATE NOT NULL                          COMMENT 'the start day of the event',
`end_date`          DATE NOT NULL                           COMMENT 'the end date of the event',
`start_time`        TIME NOT NULL                           COMMENT 'the start time of the event',
`end_time`          TIME NOT NULL                           COMMENT 'the end time of the event',
`creator_id`        INT NOT NULL                           COMMENT 'the userID',
FOREIGN KEY (`creator_id`) REFERENCES users(`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT="Contains site event information";



ALTER TABLE events
DROP FOREIGN KEY events_ibfk_1;

describe events;

select * from events;