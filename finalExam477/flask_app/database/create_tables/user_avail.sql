CREATE TABLE IF NOT EXISTS user_avail(
avail_id        INT AUTO_INCREMENT PRIMARY KEY                          COMMENT'ID for specific users availability',
user_id         INT NOT NULL                                            COMMENT'Specific users id',
event_id        INT NOT NULL                                            COMMENT'Specific event id',
date            DATE NOT NULL                                           COMMENT'data of the event',
start_time      TIME NOT NULL                                           COMMENT'start time of the event',
end_time        TIME NOT NULL                                           COMMENT'end time of the event',
avail_status    ENUM('available', 'maybe', 'unavailable') NOT NULL      COMMENT'the availability status of the user',
UNIQUE KEY user_avail(event_id, user_id, date, start_time, end_time ),
FOREIGN KEY (event_id) REFERENCES events(event_id),
FOREIGN KEY (user_id) REFERENCES users(user_id)
)ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT="Contains user availability data for an event";
