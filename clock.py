# -*- coding: utf-8 -*-
"""
Created on Sat Aug 14 15:15:38 2021

@author: imall
"""

from apscheduler.schedulers.blocking import BlockingScheduler
import model_update1
import boto

sched = BlockingScheduler(timezone='UTC')

@sched.scheduled_job('cron', day_of_week='mon-sun', hour=1)
def scheduled_job():
    model_update1.create_models()
    boto.model_upload()

sched.start()