import json
import logging
import os
import socket
from collections import defaultdict
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
log_format = '%(asctime)s %(hostname)s YOUR_APP: %(message)s'
formatter = logging.Formatter(log_format, datefmt='%b %d %H:%M:%S')
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
            group_id=grp
        )
        owed = defaultdict(lambda: 0)
        lent = defaultdict(lambda: 0)
        expense_keys = ['description', 'category_id', 'total_amount', 'group_id', 'amount']

        for key in expense.keys():
            if key not in expense_keys:
                [user_id, action] = key.split('_')
                uid = int(user_id)
                if 'owed' in action:
                    owed[uid] = expense[key] if expense[key] else 0
                else:
                    lent[uid] = expense[key] if expense[key] else 0

        for user in set(list(owed.keys()) + list(lent.keys())):
            ue = models.UserExpense.objects.create(
                user_id=user,
                amount_lent=lent[user],
                amount_owed=owed[user],
                expense=exp
            )
            print(ue.__dict__)


@shared_task(name="bulk_simplify")
def bulk_simplify(username):
    sns = boto3.client('sns')
    topic = sns.Topic(arn=os.environ.get('SNS_TOPIC'))
    message = {'email': {'DataType': 'String', 'StringValue': username}}
    topic.publish(
        Message=json.dumps(message), MessageStructure='json')
