import logging
import os
import socket
import urllib
from logging.handlers import SysLogHandler

from celery import shared_task


class ContextFilter(logging.Filter):
    hostname = socket.gethostname()

    def filter(self, record):
        record.hostname = ContextFilter.hostname
        return True


syslog = SysLogHandler(address=('logs3.papertrailapp.com', 42305))
syslog.addFilter(ContextFilter())
format = '%(asctime)s %(hostname)s YOUR_APP: %(message)s'
formatter = logging.Formatter(format, datefmt='%b %d %H:%M:%S')
syslog.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(syslog)


@shared_task(name="bulk_expense_insert")
def bulk_expenses(data):
    logger.error("This is being hit")
    with urllib.request.urlopen(data) as conn:
        s3.upload_fileobj(conn, os.environ.get('S3_BUCKET_NAME'), "transactions.csv")
    return data
