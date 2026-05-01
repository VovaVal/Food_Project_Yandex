#!/usr/bin/env python
#-*- coding: utf-8 -*-
import boto3

with boto3.session.Session(profile_name='default') as session:
    s3 = session.client(
       service_name='s3',
       endpoint_url='https://s3.cloud.ru'
    )

# Создать новый бакет
#
# # Загрузить объекты в бакет из строки
# s3.put_object(Bucket='my-bucket', Key='object_name', Body='EXAMPLE')
#
# # Загрузить объекты в бакет из файла
# s3.upload_file('website/static/imgs/product_img_default.png', 'my-bucket', 'pr.png')
# s3.upload_file('hello.txt', 'my-bucket', 'h/h.txt')

# Получить список объектов в бакете


# Получить объект
# get_object_response = s3.get_object(Bucket='my-bucket',Key='object_name')
# print(get_object_response['Body'].read())
#
# # Удалить несколько объектов
# forDeletion = [{'Key':'object_name'}, {'Key':'script/py_script.py'}]
# response = s3.delete_objects(Bucket='my-bucket', Delete={'Objects': forDeletion})

# # Удалить бакет и все объекты, включая их версии
# s3_resource = boto3.resource(
#    's3', endpoint_url='https://s3.cloud.ru/bucket-food')
# s3_bucket = s3_resource.Bucket('my-bucket')
# bucket_versioning = s3_resource.BucketVersioning('my-bucket')
# if bucket_versioning.status == 'Enabled':
#    s3_bucket.object_versions.delete()
# else:
#    s3_bucket.objects.all().delete()
#    s3_bucket.delete()

# get_object_response = s3.get_object(Bucket='bucket-food', Key='users/imgs/default_icon_user_account.png')
# print(get_object_response)
# s3.download_file('bucket-food', 'users/imgs/default_icon_user_account.png', '1.png')
s3.upload_file('1.png', 'bucket-food', '1.png')
