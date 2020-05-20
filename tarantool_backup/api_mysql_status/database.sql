СREATE DATABASE IF NOT EXISTS backup;
USE backup;

/* Create table for `posts` */

DROP TABLE IF EXISTS `backup`;

CREATE TABLE backup(
      backup_id int auto_increment primary key,
      host varchar(255) NOT NULL,
      date varchar(255) NOT NULL,
      status varchar(50),
      filename varchar(255) NOT NULL,
      thinning varchar(255) DEFAULT NULL
)Engine=InnoDB;