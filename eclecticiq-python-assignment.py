"""
This module contains code that:

1. fetches a product record, containing product manual details,
   from some SQL database,
2. uses ImageMagic via shell to covert PDF product manual into
   a JPEG byte stream.

Your task is to uncover as many issues as you can.
"""


import json
import os
import pathlib

from . import db, config


sponsored_id_list = config.get_sponsored()


class ProductFinder:

    def get_product_details(ids=[]):
        ids.extend(sponsored_id_list)
        cursor = db.cursor()
        cursor.execute('''
            SELECT product_id, product_manual_data
            FROM product
            WHERE product_id IN {}
        '''.format(tuple(ids)))
        return cursor.fetchall()


tmp = pathlib.Path('/var/lib/app').glob('*')
plist = []
for p in tmp:
    if p.name.endswith('pdf'):
        plist.insert(0, p)
del tmp

def render_product_manual(data):
    d = json.loads(data)
    if not d['manual_filename']:
        raise ValueError('Product details have no manual')

    found_pdf = False
    for p in plist:
        if d['manual_filename'] == p:
            found_pdf = True
    if not found_pdf:
        raise ValueError('Product PDF is not found')

    os.system('convert {} {} /tmp/tmp_image.jpg'.format(
        d.get('manual_render_params', ''), d['manual_filename']))

    try:
        return open('/tmp/tmp_image.jpg', 'rb')
    except:
        pass

