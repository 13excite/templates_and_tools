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
