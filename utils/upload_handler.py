import boto3
import os
from urllib.parse import urljoin

#############################################################################
#                                 VARIABLES                                 #
#############################################################################
s3_client = boto3.client('s3')

UPLOAD_BUCKET_NAME = os.environ.get('UPLOAD_BUCKET_NAME')
UPLOAD_URL_EXPIRATION = os.environ.get('UPLOAD_URL_EXPIRATION')
UPLOAD_BUCKET_ENDPOINT = os.environ.get('UPLOAD_BUCKET_ENDPOINT')


#############################################################################
#                                  FUNCTIONS                                #
#############################################################################

def upload_image(imageName):
    if not imageName:
        return None
    try:
        upload_object = s3_client.generate_presigned_post(Bucket=UPLOAD_BUCKET_NAME, Key=imageName, ExpiresIn=UPLOAD_URL_EXPIRATION)
        image_url = urljoin(UPLOAD_BUCKET_ENDPOINT, imageName)
    except Exception as err:
        print("###### Erro ao fazer upload de imagem", err)
        return None
    return {
        'uploadObject': upload_object,
        'imageUrl': image_url
    }
