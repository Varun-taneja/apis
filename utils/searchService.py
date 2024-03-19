from google.cloud import storage
from pathlib import Path
import os

path_to_private_key = 'apis/utils/fifth-compass-415612-76f634511b19.json'  

def getResumeTestData(inputPath, str_folder_name_on_gcs, localPath, privateKeyPath):
    bucketName = inputPath.split('/')[-1]
    client = storage.Client.from_service_account_json(json_credentials_path=privateKeyPath)
    bucket = storage.Bucket(client, bucketName)
    # Create the directory locally
    Path(os.path.join(localPath, str_folder_name_on_gcs)).mkdir(parents=True, exist_ok=True)

    blobs = bucket.list_blobs(prefix=str_folder_name_on_gcs)
    for blob in blobs:
        try:
            if not blob.name.endswith('/'):
                # This blob is not a directory!
                print(blob.name)
                print(f'Downloading file [{blob.name}]')
                blob.download_to_filename(f'{localPath}/{blob.name}')
        except:
            print("Unable to Download")
    return str_folder_name_on_gcs


def getJDTestData(inputPath, str_folder_name_on_gcs, localPath, privateKeyPath):
    bucketName = inputPath.split('/')[-1]
    client = storage.Client.from_service_account_json(json_credentials_path=privateKeyPath)
    bucket = storage.Bucket(client, bucketName)
    # Create the directory locally
    Path(os.path.join(localPath, str_folder_name_on_gcs)).mkdir(parents=True, exist_ok=True)

    blobs = bucket.list_blobs(prefix=str_folder_name_on_gcs)
    for blob in blobs:
        try:
            blobName = blob.name.split('/')
            if len(blobName) == 2:
                # This blob is not a directory!
                print(f'Downloading file [{blob.name}]')
                blob.download_to_filename(f'{localPath}/{blob.name}')
        except:
            print("Unable to Download")
                    
    return str_folder_name_on_gcs

def obtain_test_data(category, localFolder, inputPath):
    if category == "resume":
        Path(localFolder).mkdir(parents=True, exist_ok=True)
        try:
            getResumeTestData(inputPath, "RESUME/test-data", localFolder, path_to_private_key)
            getResumeTestData(inputPath, "/", localFolder, path_to_private_key)
        except:
            return "Record not found", 400
    elif category == "job":
        Path(localFolder).mkdir(parents=True, exist_ok=True)
        try:
            getJDTestData(inputPath, "JD/", localFolder, path_to_private_key)
            getResumeTestData(inputPath, "/", localFolder, path_to_private_key)
        except:
            return "Record not found", 400
    else:
        #return jsonify({"status": "Bad Request Please check category should be either resume or job!"})
        return "Record not found", 400
# obtain_test_data("resume", "data/resumes", "https://console.cloud.google.com/storage/browser/hackathon1415")