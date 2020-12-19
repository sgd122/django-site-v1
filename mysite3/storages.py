from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

# for media
class S3DefaultStorage(S3Boto3Storage):
    # default_acl = "private"
    # bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    location = "media"


# for static
class S3StaticStorage(S3Boto3Storage):
    # bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    # default_acl = "public-read"
    location = "static"
