#!/usr/bin/python3
import os
import pathlib
import time
# import boto3
import re
from tempfile import NamedTemporaryFile
# import mammoth  # docx
import botocore
import fitz
import sys
import openai
import tempfile
import itertools
from langchain.document_loaders import UnstructuredFileLoader
from langchain.document_loaders import UnstructuredPowerPointLoader
from langchain.document_loaders import UnstructuredWordDocumentLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
import pandas as pd
from psycopg2 import sql
from environments import s3, connection, bucket, tempfolder,
import cgi
import nltk
from dotenv import load_dotenv

nltk.data.path.append('/usr/bin/nltk_data/')

fs = cgi.FieldStorage()
d = {}
for k in fs.keys():
    d[k] = fs.getvalue(k)

token = d['token']
task1 = d['task']




def download_file(path,key):
    try:
        s3 = boto3.resource('s3',
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key,
                            region_name=region_name,
                            endpoint_url=endpoint_url)

        s3.Bucket(bucket).download_file(path+key, tempfolder+key)
        return tempfolder+key
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            return None
        else:
            raise


def convert_to_txt(basename, file):
    doc = fitz.open(file)
    text = ''
    for page in doc:
        text += page.get_text()
    with open(tempfolder + basename + ".txt", "wt") as f:
        f.write(text)


def db_save(documents, file):
    if aivendor == "azureopenai":
        db = FAISS.from_documents(documents, OpenAIEmbeddings(chunk_size=1)) #because the chunk size can be 1
        db.save_local('data/' + namespace)
    elif aivendor == "openai":
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)
        db = FAISS.from_documents(texts, embeddings)
        db.save_local('data/' + namespace)

    os.remove(file)
    query = sql.SQL("INSERT INTO {schema}.audit (prospect, reference, action, username, field, value)"
                    " VALUES (%s,%s,%s,%s,%s,%s)").format(schema=sql.Identifier(schema))
    mycursor.execute(query, (file, '999', 'Indexing AI files', username, file, '999'))


# while True:
try:
    #if task1 == "rfpreader":
    mycursor = connection.cursor()
    queryz = sql.SQL(
        "select uid,username,email,schema,domain,folder,aivendor,task,col1,col2,col3,col4,col5,col6 from "
        "connection.pytemp WHERE task='rfpreader' "
        "order by uid desc limit 1").format()
    mycursor.execute(queryz, )
    results = mycursor.fetchone()
    print(results)
    numrows = mycursor.rowcount
    if numrows == 1:
        uid = int(results[0])
        username = str(results[1])
        email = str(results[2])
        schema = str(results[3])
        domain = str(results[4])
        folder = str(results[5])
        aivendor = str(results[6])
        task = str(results[7])
        product = str(results[8])  # col1
        region = str(results[9])
        recordtype = str(results[10])
        language = str(results[11])
        namespace = str(results[12] + results[13])
        if aivendor == "azureopenai":
            def load_env_for_tenant(folder):
                env_file = f"{'keys/' + folder}.env"
                load_dotenv(env_file)

            load_env_for_tenant(folder)
            OPENAI_API_TYPE = os.environ["OPENAI_API_TYPE"]
            OPENAI_API_VERSION = os.environ["OPENAI_API_VERSION"]
            OPENAI_API_BASE = os.environ["OPENAI_API_BASE"]
            OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

        queryz = sql.SQL(
            "select keyid,value,value1,value2,value3,value4,value5 from {schema}.{table} WHERE "
            "tablename ='openaiparams'").format(
            schema=sql.Identifier(schema),
            table=sql.Identifier('reference'))
        mycursor.execute(queryz, )
        param = mycursor.fetchone()
        modelname = param[0]  # ada - babage
        responsemode = param[1]  # stuff, map-reduce
        openai.api_key = param[2]  # openai api
        aimatching = param[3]  # UM - only unmatched, NP - Not Processed, NONFM - non full match
        assignedto = param[4]  # assign generated response to Responder. Reviewer, Bid Manager

        embeddings = OpenAIEmbeddings(openai_api_key=openai.api_key)
        path = product + "-" + region + "-" + recordtype + "-" + language + "/"
        input_path = folder + "/repository/" + path.replace(" ", "")
        filelist = []
        queryx = sql.SQL(
            "select value1,value2 from {schema}.{table} WHERE "
            "tablename ='indexerfiles' and value2='N';").format(
            schema=sql.Identifier(schema),
            table=sql.Identifier('reference'))
        mycursor.execute(queryx, )
        files = mycursor.fetchall()
        for file in files:
            filelist.append(file[0])

        if len(filelist) > 0:
            for filename in filelist:  # take 3 files and process for this 5 minute cycle.
                # for filename in filelist[-3:]:  # take 3 files and process for this 5 minute cycle.
                file = download_file(input_path, filename)
                if file is not None:
                    split = os.path.splitext(file)
                    basename = pathlib.Path(file).stem
                    filetype = split[1]
                    if filetype != ".xlsx" or ".csv":
                        loader = UnstructuredFileLoader(file)
                        data = loader.load()
                        db_save(data, file)

                    query = sql.SQL("INSERT INTO {schema}.notification (link,message,username,flag)"
                                    " VALUES (%s,%s,%s,%s)").format(
                        schema=sql.Identifier(schema))
                    txt = filename + " has been uploaded into the repository"
                    mycursor.execute(query, (
                        "Past Documents", txt, username, "UR"))

                    query = sql.SQL("update {schema}.reference set value2='Y' where tablename=%s"
                                    " and value1=%s").format(
                        schema=sql.Identifier(schema))
                    mycursor.execute(query, ("indexerfiles", filename))
                    # s3.Object(bucket, filename).delete()
            sender = 'support@rfp.plus'
            msg['Subject'] = 'Uploaded files'
            msg['From'] = sender
            msg['To'] = email
            html_message = MIMEText('Hello ' + username + '<br><br>The file/s ' + str(filelist) + ' you submitted for '
                                    'uploading is indexed. You can start searching for its contents.'
                                    '<br><br>Regards,<br>RFP Plus Support team.',
                                    'html')
            msg.attach(html_message)
            mailServer.ehlo()
            mailServer.starttls()
            mailServer.ehlo()
            mailServer.login(euname, pval)
            mailServer.sendmail(sender, email, msg.as_string())
            mailServer.close()

            query = sql.SQL("Delete from connection.pytemp where uid=%s and task=%s").format(
                table=sql.Identifier('pytemp'))
            mycursor.execute(query, (uid, task))

            connection.commit()
            mycursor.close()
            print('done')
    # time.sleep(300)

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
