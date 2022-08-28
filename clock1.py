# -*- coding: utf-8 -*-
"""
Created on Sat Aug 14 15:15:38 2021

@author: imall
"""

import model_update1
import boto


def scheduled_job():
    model_update1.create_models()
    boto.model_upload()

scheduled_job()
