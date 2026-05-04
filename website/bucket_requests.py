#!/usr/bin/env python
#-*- coding: utf-8 -*-
import boto3

from website.config import BUCKET_NAME
from flask_login import current_user


__factory = None


def create_bucket_session():
    """Создаёт и возвращает S3-клиент для работы с бакетом"""
    session = boto3.session.Session(profile_name='default')
    s3_client = session.client(
        service_name='s3',
        endpoint_url='https://s3.cloud.ru'
    )
    return s3_client

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
# s3.upload_file('1.png', 'bucket-food', '1.png')


def upload_img_user(img):
    if current_user.img != 'users/imgs/default_icon_user_account.png':
        resp = delete_by_key(current_user.img)

        if not resp:
            return False

    if not img:
        return None

    img_name = f'users/imgs/user_img_{current_user.id}'

    s3 = create_bucket_session()
    s3.upload_fileobj(
        img,
        BUCKET_NAME,
        img_name
    )

    return img_name


def upload_logo_shop(img, shop):
    if shop.logo != 'shops/logos/default_logo.svg':
        resp = delete_by_key(shop.logo)

        if not resp:
            return False

    if not img:
        return None

    img_name = f'shops/logos/shop_logo_{shop.id}'

    s3 = create_bucket_session()
    s3.upload_fileobj(
        img,
        BUCKET_NAME,
        img_name
    )

    return img_name


def delete_by_key(key: str) -> bool:
    """Удаляет файл из S3 по ключу (пути внутри бакета)"""
    if not key:
        return True

    try:
        bucket_name = BUCKET_NAME
        s3 = create_bucket_session()
        s3.delete_object(Bucket=bucket_name, Key=key)
        return True

    except Exception as e:
        print('Error occurred while deleting file!')
        return False