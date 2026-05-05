#!/usr/bin/env python
#-*- coding: utf-8 -*-
import boto3
import uuid

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


def upload_img_shop(img, shop, filename):
    # if shop.logo != 'shops/logos/default_logo.svg':
    #     resp = delete_by_key(shop.logo)
    #
    #     if not resp:
    #         return False

    if not img:
        return None

    img_name = f'shops/imgs/shop_img_{uuid.uuid4().hex}'

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