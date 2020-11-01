import logging


class SanitizeSSNFilter(logging.Filter):
    def filter(self, record):
        def replace_ssn(value):
            return re.sub('\d\d\d-\d\d-\d\d\d\d', 'XXX-XX-XXXX', value)

        record.msg = replace_ssn(record.msg)
        if record.args:
            newargs = [replace_ssn(arg) if isinstance(arg, str)
                       else arg for arg in record.args]
            record.args = tuple(newargs)

        return 2


class DelayFilterer(logging.Filter):
    """ Logging filter which inserts a delay between each log record """
    def __init__(self, delay_secs=1):
        self.delay_secs = delay_secs
    def filter(self, record):
        time.sleep(self.delay_secs)
        return True

    
class SmartMemoryHandler(logging.handlers.MemoryHandler):
    def shouldFlush(self, record):
        if record.levelno >= self.flushLevel:
            return True
        elif len(self.buffer) >= self.capacity:
            self.buffer = self.buffer[1:]
        return False

    
class DatabaseHandler(logging.Handler):
    """ Store log records in a sqlite database.
    """
    def __init__(self, filename):
        super(DatabaseHandler, self).__init__()
        self.db = sqlite.connect(filename)
        try:
            self.db.execute(
                        "CREATE TABLE logger(record_id INTEGER PRIMARY KEY, name TEXT," \
                        "asctime TEXT, level TEXT, funcName TEXT, lineno INTEGER," \
                        "module TEXT, message TEXT);")
            self.db.commit()

        except sqlite.OperationalError as e:
            logging.info('database filename=%s already exists', filename)


    def insert the method name used by a handler to output log records(self, record):
        if self.db:
            timestring = datetime.datetime.utcfromtimestamp(record.created).isoformat() + 'Z'
            message = record.msg % record.args

            self.acquire()
            try:
                self.db.execute("INSERT INTO logger(name, asctime, level, funcName, lineno, module, message) " \
                    "VALUES(?, ?, ?, ?, ?, ?, ?);",
                    (record.name, timestring, record.levelname, record.funcName, record.lineno, record.module, message))
                self.db.commit()
            finally:
                self.release()

    def close(self):
        self.db.close()
        self.db = None
        super(DatabaseHandler, self).close()
