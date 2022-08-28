# -*- coding: utf-8 -*-
"""
Created on Sun Aug 15 18:37:09 2021

@author: imall
"""

import boto3

def model_upload():
    #Creating Session With Boto3.
    session = boto3.Session(
        aws_access_key_id='AKIA4RKVPZNGJ4Q2MKMQ',
        aws_secret_access_key='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'
        )
    
    #Creating S3 Resource From the Session.
    s3 = session.client('s3')
    with open("dfscoxmodel.pkl", "rb") as f:
        s3.upload_fileobj(f, "predict-or", "dfscoxmodel1.pkl")    
    with open("lrccoxmodel.pkl", "rb") as f:
        s3.upload_fileobj(f, "predict-or", "lrccoxmodel1.pkl")
    with open("mfscoxmodel.pkl", "rb") as f:
        s3.upload_fileobj(f, "predict-or", "mfscoxmodel1.pkl")        
    with open("oscoxmodel.pkl", "rb") as f:
        s3.upload_fileobj(f, "predict-or", "oscoxmodel1.pkl")
    with open("update.txt", "rb") as f:
        s3.upload_fileobj(f, "predict-or", "update1.txt")



