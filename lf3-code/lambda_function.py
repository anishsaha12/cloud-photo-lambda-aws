import json
import boto3

def lambda_handler(event, context):
    collection_id_name = "hw2-my-faces-collection"
    rekognition_client=boto3.client('rekognition')
    
    response= rekognition_client.create_collection(CollectionId=collection_id_name)
    print(response)
    
    
    # response=rekognition_client.delete_collection(CollectionId=collection_id_name)
    # print(response)

    return 
