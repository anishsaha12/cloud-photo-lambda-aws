import boto3
import json
import requests
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection

def lambda_handler(event, context):
    print(event)
    
    insert_bucket = event["Records"][0]["s3"]["bucket"]["name"]
    insert_key = event["Records"][0]["s3"]["object"]["key"]
    custom_labels = []
    
    ho = boto3.client("s3").head_object(Bucket=insert_bucket, Key=insert_key)
    
    client=boto3.client('rekognition')

    response = client.detect_labels(Image={'S3Object':{'Bucket':insert_bucket,'Name':insert_key}},
        MaxLabels=50)

    detected_labels = []

    for label in response["Labels"]:
        detected_labels.append(label['Name'])
        
    all_labels = detected_labels + custom_labels
    
    timestamp_datetime = ho["LastModified"]
    timestamp_string = timestamp_datetime.strftime("%Y-%m-%dT%H:%M:%S")


    es_json = {
        "objectKey": insert_key,
        "bucket": insert_bucket,
        "createdTimestamp": timestamp_string,
        "labels": all_labels
        }
        
    print(es_json)
    
      
    # es_json =   {
    #                 "objectKey": "columbia_1.png",
    #                 "bucket": "bucketb2",
    #                 "createdTimestamp": "2021-02-17T16:22:36",
    #                 "labels": [
    #                     "Person",
    #                     "Human",
    #                     "Building",
    #                     "Campus",
    #                     "Urban",
    #                     "People",
    #                     "City",
    #                     "Town",
    #                     "Downtown",
    #                     "Architecture",
    #                     "Grass",
    #                     "Plant",
    #                     "Field",
    #                     "Vegetation",
    #                     "Amphitheatre",
    #                     "Arena",
    #                     "Amphitheater",
    #                 ],
    #             }

    # code based on https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/es-request-signing.html#es-request-signing-python
    
    
    # region = 'us-east-1'
    # service = 'es'
    # credentials = boto3.Session().get_credentials()
    # awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    
    # host = "search-photos-7ka2227iannxvqedwmlx62ft7u.us-east-1.es.amazonaws.com"
    
    # es = Elasticsearch(
    #     hosts = [{'host': host, 'port': 443}],
    #     http_auth = awsauth,
    #     use_ssl = True,
    #     verify_certs = True,
    #     connection_class = RequestsHttpConnection
    # )
    

    # es.index(index="photos", id=es_json["objectKey"], body=es_json)
    
    
    return None


