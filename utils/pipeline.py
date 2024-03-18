import os
import pymongo
from google.cloud import storage
from utils.searchService import obtain_test_data
from utils.end2end import *
from pymongo import MongoClient


def getAzureClient():
  client = AzureOpenAI(
    azure_endpoint = 'https://sunflower-openai.openai.azure.com/',
    api_key='f68dfd696b2a4917a892e81276af3941',
    api_version="2024-02-01"
  )
  return client

CONNECTION_STRING = "mongodb+srv://admin:admin123@sunflowercluster.oppjzec.mongodb.net/"

# Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
client_mongo = MongoClient(CONNECTION_STRING)
mongo_database = client_mongo["SunflowerDB"]

resume_collection = mongo_database["ResumeTest"]
jd_collection = mongo_database["JDTest"]

def runPipelineForResume(inputPath):
    # Obtain test data
    test_data_folder = "data"
    obtain_test_data("resume", os.path.join(test_data_folder, "resumes"), inputPath)
    # Process resume test data
    resume_paths = get_all_files(os.path.join(test_data_folder, "resumes"))
    put_raw_data_on_mongodb(resume_collection, resume_paths)
    gpt_responses_resume = put_gpt_responses_on_mongodb(resume_collection, prompt_begin_resume, prompt_specifications_resume)
    create_resume_search_index()
    put_embeddings_on_search_client_resume(resume_collection,"resume-index",endpoint_search_client,credential_search_client)

def runPipelineForJD(inputPath):
    test_data_folder = "data"
    obtain_test_data("job", os.path.join(test_data_folder, "jds"), inputPath)
    # Process jd test data
    jd_paths = get_all_files(os.path.join(test_data_folder, "jds"))
    put_raw_data_on_mongodb(jd_collection, jd_paths)
    gpt_responses_jd = put_gpt_responses_on_mongodb(jd_collection, prompt_begin_jd, prompt_specifications_jd)
    create_jd_search_index()
    put_embeddings_on_search_client_jd(jd_collection,"jd-index", endpoint_search_client, credential_search_client)

