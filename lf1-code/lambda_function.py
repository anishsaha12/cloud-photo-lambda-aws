import boto3
import json
import requests
# import random
# import cv2
# import string
# import numpy as np
import inflect
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection

def lambda_handler(event, context):
    print(event)

    
    insert_bucket = event["Records"][0]["s3"]["bucket"]["name"]
    insert_key = event["Records"][0]["s3"]["object"]["key"]
    
    ho = boto3.client("s3").head_object(Bucket=insert_bucket, Key=insert_key)
    
    client=boto3.client('rekognition')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table("hw2-faces-index-dynamodb")
    collection_id_name = "hw2-my-faces-collection"

    try:
        raw_labels = ho["Metadata"]["customlabels"]
        custom_labels = raw_labels.split(', ')
    except:
        raw_labels = ''
        custom_labels = []

    # Code based on tutorial: https://aws.amazon.com/blogs/machine-learning/build-your-own-face-recognition-service-using-amazon-rekognition/    
    if 'name_' in raw_labels:                               # if user provides name
        input_name_tag = custom_labels[-1][5:]
        custom_labels = custom_labels[:-1] + [input_name_tag]
        print('name', input_name_tag)
        
        response = client.index_faces(
            Image={
                "S3Object": {
                    "Bucket": insert_bucket,
                    "Name": insert_key
                }
            },
            CollectionId=collection_id_name
        )
                
        print("rekognition_client response : {}".format(response))
                
        face_id = response['FaceRecords'][0]['Face']['FaceId']
    
        r = {
            "FaceId": face_id,
            "name_tag": input_name_tag
        }
        
        response = table.put_item(Item=r)
        
        print("dynamodb put response :{}".format(response))
    
    else:                   # user doesn't provide name -> auto detect name if existing already
        response = client.search_faces_by_image(
            CollectionId=collection_id_name,
    		Image={
    		    "S3Object":{"Bucket": insert_bucket, "Name": insert_key}
    		}
        )
    
        detected_name_tags = []
        
        for match in response['FaceMatches']:
            print(match['Face']['FaceId'],match['Face']['Confidence'])
            f_id = match['Face']['FaceId']
            response = table.get_item(Key={'FaceId': f_id})
            detected_name_tags.append(response['Item']['name_tag'])

        detected_name_tags = list(set(detected_name_tags))
        
        custom_labels += detected_name_tags
        print("detected_name_tags: {}".format(detected_name_tags))
        # insert_processing_bucket = "hw2-processing-bucket" 
        # s3_resource = boto3.resource('s3')
    
        # bucket = s3_resource.Bucket(insert_bucket)
        # img = bucket.Object(insert_key).get().get('Body').read()
        # image = cv2.imdecode(np.asarray(bytearray(img)), cv2.IMREAD_COLOR)
    
        # response = client.detect_faces(Image={"S3Object":{"Bucket": insert_bucket, "Name": insert_key}})
        # all_faces=response['FaceDetails']
    
    
        # image_width = np.shape(image)[1]
        # image_height = np.shape(image)[0]
    
        # detected_name_tags = []
    
        # for face in all_faces:
        #     box=face['BoundingBox']
        #     x1 = int((box['Left'] * image_width) * 0.9)
        #     y1 = int((box['Top'] * image_height) * 0.9)
        #     x2 = int((box['Left'] * image_width + box['Width'] * image_width) * 1.10)
        #     y2 = int((box['Top'] * image_height + box['Height']  * image_height) * 1.10)
    
        #     image_crop = image[y1:y2, x1:x2]
    
        #     data_serial = cv2.imencode('.png', image_crop)[1].tostring()
            
        #     letters = string.ascii_lowercase
        #     f_name = ''.join(random.choice(letters) for i in range(10)) +'.png'
            
        #     s3_resource.Object(insert_processing_bucket, f_name).put(Body=data_serial,ContentType='image/PNG')
    
        #     response = client.search_faces_by_image(
        #         CollectionId=collection_id_name,
        #         Image={"S3Object":{"Bucket": insert_processing_bucket, "Name": f_name}}
        #         )
    
        #     # s3_resource.Object(insert_processing_bucket, f_name).delete()
    
        #     for match in response['FaceMatches']:
        #         f_id = match['Face']['FaceId']
        #         response = table.get_item(Key={'FaceId': f_id})
        #         detected_name_tags.append(response['Item']['name_tag'])
        
        # custom_labels += detected_name_tags
        # print(detected_name_tags)
        
    print('all_c_labels', custom_labels)

    response = client.detect_labels(Image={'S3Object':{'Bucket':insert_bucket,'Name':insert_key}},
        MaxLabels=50)

    detected_labels = []

    for label in response["Labels"]:
        detected_labels.append(label['Name'])
        
    all_labels = detected_labels + custom_labels
    
    ## Convert Plurals to Singulars
    inflect_p = inflect.engine()
    final_labels = []
    for label in all_labels:
        res = inflect_p.singular_noun(label)
        if res==False:
            final_labels.append(label)
        else:
            final_labels.append(res)
    
    print('All Labels Final (after inflection):', final_labels)
    
    timestamp_datetime = ho["LastModified"]
    timestamp_string = timestamp_datetime.strftime("%Y-%m-%dT%H:%M:%S")


    es_json = {
        "objectKey": insert_key,
        "bucket": insert_bucket,
        "createdTimestamp": timestamp_string,
        "labels": final_labels
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
    
    
    region = 'us-east-1'
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    
    host = "search-hw2-photos-elastic-search-ehac5wtt5wwksboszvgj5gbynq.us-east-1.es.amazonaws.com"
    
    es = Elasticsearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    

    es.index(index="photos", id=es_json["objectKey"], body=es_json)
    
    
    return None


