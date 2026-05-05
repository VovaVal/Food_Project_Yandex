#!/usr/bin/env python
#-*- coding: utf-8 -*-
import boto3
import random

from website.config import BUCKET_NAME
from flask_login import current_user


__factory = None
letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V',
           'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r',
           's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '!', '#', '$',
           '%', '&', '*', '+', '.', ':', ';', '<', '=', '>', '?', '@', '_']


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

    img_name = f'shops/imgs/shop_img_{''.join(random.choices(letters, k=20))}'

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