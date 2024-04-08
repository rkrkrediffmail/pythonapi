#!/usr/bin/env python3
import os
import sys
import psycopg2
import boto3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
sys.stdout.write("Content-Type: application/json")
sys.stdout.write("\n")
sys.stdout.write("\n")

euname = 'support@rfp.plus'
pval = 'c10ZUw17XEPYMBJE'
msg = MIMEMultipart('mixed')
mailServer = smtplib.SMTP('mail.smtp2go.com', 2525)

aws_access_key_id = 'TWJRKKNYNJFMBQMJSOY2'
aws_secret_access_key = 'JmCq8Q1Bt7PjUdqc8f8IfGvryzSPJ0VRuJWAR5dPSH4'
bucket = 'clientfile'
region_name = 'ams3'
endpoint_url = 'https://ams3.digitaloceanspaces.com'

"""SERVERNAME = 'db-postgresql-blr1-57966-do-user-8079576-0.b.db.ondigitalocean.com'
DATABASE = 'rfp'
USERNAME = 'doadmin'
PASSWORD = 'AVNS_IuTFRlMu0ojxD9B7rBH'
sslmode = 'require'
PORT = 25060"""

SERVERNAME = 'azure-rfpplus.postgres.database.azure.com'
DATABASE = 'rfp'
USERNAME = 'doadmin'
PASSWORD = '31Jan1976$'
sslmode = 'require'
PORT = 5432


#SERVERNAME = 'db-postgresql-ams3-39349-do-user-8079576-0.b.db.ondigitalocean.com'
#DATABASE = 'rfp'
#USERNAME = 'doadmin'
#PASSWORD = 'AVNS_WqVsPS5Wtwf8fCd'
#sslmode = 'require'
#PORT = 25060

CONNECTION_STRING=str(f"postgresql://doadmin:"+PASSWORD+"@"+SERVERNAME+":"+str(PORT)+"/"+DATABASE+"?sslmode="+sslmode)


tempfolder = str("/"+"t"+"m"+"p"+"/")


try:
    connection = psycopg2.connect(host=SERVERNAME, dbname=DATABASE, user=USERNAME, password=PASSWORD, port=PORT,
                                  sslmode=sslmode)
except (Exception, psycopg2.DatabaseError) as error:
    print(error)

s3 = boto3.resource('s3',
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=region_name,
                    endpoint_url=endpoint_url)

azure_connection_string = "DefaultEndpointsProtocol=https;AccountName=rfpplusazure;AccountKey=045GQO67sFzEiB0rykictrIwai4liqFz3qee5HzVn1i6BM8BhvwsIS0clmUiTXp8CAn6BVats9ia+ASt5aKI3w==;EndpointSuffix=core.windows.net"
container_name = "temenos"
