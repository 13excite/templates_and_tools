SELECT backup_id, host, date, filename
FROM backup
WHERE STR_TO_DATE(date, '%Y-%m-%d %H-%i-%S') < CURDATE()-INTERVAL 5 DAY
AND
TIME(STR_TO_DATE(date, '%Y-%m-%d %H-%i-%S')) <= '19:00:00';
