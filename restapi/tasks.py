from collections import defaultdict
import logging
import os
import socket
import urllib
from logging.handlers import SysLogHandler
import boto3
from celery import shared_task
from restapi import models


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
    for expense in data:
        print(expense.keys())
        grp = None
        if 'group_id' in expense:
            grp = expense['group_id']
        exp = models.Expense.objects.create(
            description=expense['description'],
            category_id=expense['category_id'],
            total_amount=expense['amount'],
            )
        print(exp.category)
        owed = defaultdict(lambda: 0)
        lent = defaultdict(lambda: 0)
        for key in expense.keys():
            if key in [
                'description',
                'category_id',
                'total_amount',
                'group_id',
                    'amount']:
                continue
            if 'owed' in key:
                owed[int(key.split('_')[0])
                     ] = expense[key] if expense[key] else 0
            else:
                lent[int(key.split('_')[0])
                     ] = expense[key] if expense[key] else 0
        for user in set(list(owed.keys()) + list(lent.keys())):
            if lent[user] or owed[user]:
                ue = models.UserExpense.objects.create(
                    user_id=user,
                    amount_lent=lent[user],
                    amount_owed=owed[user],
                    expense=exp
                )

                print(ue.__dict__)
