# набор скриптов и сервисов для бекапа тарантулов

- **backup_tarantool.py**
 Основной скрипт бекапа
Юзать так. Но нужно будет добавить поддержку конфига, и вынести туда урлы и прочее
```
backup_cleaner.py
```
- **/usr/site/bin/check_tnt_longterm_status.py**
Чекалка проверки статусов бекапов
```
/usr/site/bin/check_tnt_longterm_status.py -o /tmp/monitoring_file.status
```
- **backup_cleaner.py**
Удалятор бекапов, оставляет только последнйи бекап за сутки.
```
backup_cleaner.py -c cleaner.ini
cat clenaer.ini
```

- **api_mysql_status**
Гошный сервис для бекапов. Собирается автоматом.
1. Ручки
   - /create POST - создаем статус бекапов в базе. В теле передаем json
   - /status GET - получаем статус сфейленных бекапов если такие есть
   - /thinning GET -  получаем массив хешей бекепаов, которые нужно будет почистить
   - /update/{backup_id} POST - обновляем статус для бекапа, кооторый был удалн при прореживании. Id - это значение поля backup_id полученное из базы 

