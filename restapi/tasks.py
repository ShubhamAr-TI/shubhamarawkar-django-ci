from celery import shared_task
import os
import boto3
from subprocess import call
import urllib
import requests

@shared_task(name="bulk_expense_insert")
def bulk_expenses(data):
    print("bulk_expenses",data)
    return data
