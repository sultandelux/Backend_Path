from typing import BinaryIO
import logging
import boto3


class S3Service:
    def __init__(self):
        self.s3 = boto3.client("s3")

    def upload_file(self, file: BinaryIO, filename: str):
        bucket = "galluppublic"
        filekey = f"posts/{filename}"

        self.s3.upload_fileobj(file, bucket, filekey, ExtraArgs={'ACL': 'public-read'})

        bucket_location = boto3.client("s3").get_bucket_location(Bucket=bucket)
        object_url = "https://s3-{0}.amazonaws.com/{1}/{2}".format(
            bucket_location["LocationConstraint"], bucket, filekey
        )

        return object_url
    
    def upload_file_path(self, filepath: str, filename: str):
        bucket = "galluppublic"
        filekey = f"posts/{filename}"

        with open(filepath, "rb") as file_obj:
            self.s3.upload_fileobj(file_obj, bucket, filekey, ExtraArgs={'ACL': 'public-read'})

        bucket_location = boto3.client("s3").get_bucket_location(Bucket=bucket)
        object_url = "https://s3-{0}.amazonaws.com/{1}/{2}".format(
            bucket_location["LocationConstraint"], bucket, filekey
        )

        return object_url
    
    #get txt 

    def get_file_string(self, filekey: str):
        bucket = "galluppublic"
         
        s3_response = boto3.client('s3').get_object(Bucket=bucket, Key=filekey)
        s3_object_body = s3_response.get('Body')
        content_str = s3_object_body.read().decode()
        return content_str




    # delete file
    def delete_file(self, filename: str):
        bucket = "galluppublic"
        filekey = f"posts/{filename}"
        self.s3.delete_object(Bucket=bucket, Key=filekey)
        return True
