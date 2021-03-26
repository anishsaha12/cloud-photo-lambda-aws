import boto3
import json
import inflect
import requests
from requests_aws4auth import AWS4Auth

def lambda_handler(event, context):
    print(event['params']['querystring']['q'])
    client = boto3.client('lex-runtime')
    
    data = event['params']['querystring']['q']
    # data = "Show me a cat"
    
    response = client.post_text(
        botName='disambiguator',
        botAlias='prod',
        userId='id1',
        inputText= data
    )
    
    labels_ini = []
    
    try:
        if response["intentName"] == "searchintent":
            for slot in response["slots"]:
                e = response["slots"][slot]
                if e is not None:
                    labels_ini.append(e)
    except:
        labels_ini = []
        
    ## Convert Plurals to Singulars
    inflect_p = inflect.engine()
    labels = []
    for label in labels_ini:
        res = inflect_p.singular_noun(label)
        if res==False:
            labels.append(label)
        else:
            labels.append(res)
    
    print('Labels (after inflection):', labels)

    
    # labels = ["cat", "dog"]
    # labels = ["dog"]


    region = 'us-east-1'
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    ## CHANGE
    host = 'search-hw2-photos-elastic-search-ehac5wtt5wwksboszvgj5gbynq.us-east-1.es.amazonaws.com' # For example, search-mydomain-id.us-west-1.es.amazonaws.com
    index = 'photos'
    url = 'https://' + host + '/' + index + '/_search'
    headers = { "Content-Type": "application/json" }
    

    es_query_string = ""
    if len(labels) >=1 :
        es_query_string = "(" + labels[0] + ")"
        for i in range(len(labels) - 1):
            es_query_string = es_query_string + " OR (" + labels[i+1] + ")"
            
            

    query = {
        "size": 10,        
        "query": {
            "query_string": {
              "default_field": "labels",
              "query": es_query_string
            }
          }
    }
    
    r = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query)).json()
    
    search_result_list = r["hits"]["hits"]
    
    matching_images_loc = []
    
    # search_result_list = [
    #     {
    #         "_source": {
    #             "objectKey": "116227.jpg",
    #             "bucket": "hw2-b2-photos",
    #             "labels": [
    #                 "Person",
    #                 "Human",
    #                 "Building",
    #                 "Campus",
    #                 "Urban"
    #             ]
    #         }
    #     },
    #     {
    #         "_source": {
    #             "objectKey": "116341.jpg",
    #             "bucket": "hw2-b2-photos",
    #             "labels": [
    #                 "People",
    #                 "City",
    #                 "Town",
    #                 "Downtown"
    #             ]
    #         }
    #     },
    #     {
    #         "_source": {
    #             "objectKey": "117173.jpg",
    #             "bucket": "hw2-b2-photos",
    #             "labels": [
    #                 "Architecture",
    #                 "Grass",
    #                 "Plant",
    #                 "Field"
    #             ]
    #         }
    #     },
    #     {
    #         "_source": {
    #             "objectKey": "117346.jpg",
    #             "bucket": "hw2-b2-photos",
    #             "labels": [
    #                 "Vegetation",
    #                 "Amphitheatre",
    #                 "Arena",
    #                 "Amphitheater",
    #             ]
    #         }
    #     }
    # ]
    
    for result in search_result_list:
        image_name = result["_source"]["objectKey"]
        bucket_name = result["_source"]["bucket"]
        labels_list = result["_source"]["labels"]
        
        matching_images_loc.append({
            'url': 'https://'+bucket_name+'.s3.amazonaws.com/'+image_name,
            'labels': labels_list
        })
        
    print(matching_images_loc)

    return {
        'results': matching_images_loc,
    }





