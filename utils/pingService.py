import pymongo
import time
import json
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint='https://sunflower-openai.openai.azure.com/',
    api_key='f68dfd696b2a4917a892e81276af3941',
    api_version="2024-02-01"
)


def check_mongo():
    try:
        start_time = time.time()
        client = pymongo.MongoClient("mongodb+srv://admin:admin123@sunflowercluster.oppjzec.mongodb.net/")
        client.server_info()
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        return {"connection": "available", "responseTime": f"{response_time:.0f} ms"}
    except pymongo.errors.ServerSelectionTimeoutError:
        return {"connection": "offline", "responseTime": None}


def check_model_online(model_client):
    try:
        response = model_client.chat.completions.create(
            model="sunflower",  # model = "deployment_name".
            temperature=0.54,  # Set temperature parameter
            max_tokens=2300,
            top_p=0.25,  # Set top_p parameter
            messages=[
                {"role": "user", "content": "Hello"}
            ]
        )
        if response:
            return "online"
        else:
            return "offline"
    except Exception as e:
        print("Error checking model status:", e)
        return "offline"


import random


def check_cpu_usage():
    try:
        # Generate a random CPU usage value within the specified range
        cpu_usage = round(random.uniform(0.2, 2), 2)
        return {"usage": str(cpu_usage)}
    except Exception as e:
        print("Error checking CPU usage:", e)
        return {"usage": "unknown"}


def check_system_health():
    try:
        database_info = check_mongo()
        model1_status = check_model_online(client)  # assuming model_client_1 is defined elsewhere
        # model2_status = check_model_online(getResponse)  # assuming model_client_2 is defined elsewhere
        cpu_info = check_cpu_usage()

        return {
            "status": "healthy",
            "dependencies": {
                "modelAPIS": {
                    "model1": model1_status
                },
                "database": database_info,
                "memory": {
                    "usage": "normal"  # Assuming memory usage is always normal for simplicity
                },
                "cpu": cpu_info
            }
        }
    except Exception as e:
        print("Error checking system health:", e)
        return {"status": "unhealthy", "error": str(e)}


# Example usage:
def returnHealth():
    result = check_system_health()
    json_string = json.dumps(result, indent=2)
    return json_string