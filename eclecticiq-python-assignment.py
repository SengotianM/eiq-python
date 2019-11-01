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

# Using absolute imports instead of relative imports, helps in
# avoiding any or all package name clashes.
from . import db, config

# Avoid using a global variable. There are two ways to get the
# variable,
# 1. Make it member variable to ProductFinder class and init
#    while you initialize the class instance
# 2. Convert fetching function below to private method of the
#    class. This applies only if the intended use of the list
#    is within the class.
sponsored_id_list = config.get_sponsored()

# Please see the comments below for converting the fetching
# function from global to more local and still accessible
# form
class ProductFinder:
    # -----------------------------------------------------
    # Method # 1
    # def __init__(self):
    #   self.sponsored_id_list = config.get_sponsored
    #  
    #  OR
    #
    # Method # 2
    # def __get_sponsored_id_list(self):
    #   return config.get_sponsored()
    # -----------------------------------------------------
    
    def get_product_details(
        # self, # Class method needs to have 'self' as first parameter
        ids=[]
    ):
        # ids.extend(self.__get_sponsored_id_list())
        ids.extend(sponsored_id_list)
        cursor = db.cursor()

        # Query can be formed separately instead of writing it
        # as part of the cursor.execute()
        # Example:
        # -----------------------------------------------------
        # query = "SELECT 
        #       product_id, product_manual_data 
        #       FROM product 
        #       WHERE product_id IN %(product_ids)s"
        #
        # product_ids = tuple(ids)
        # cursor.execute(query, (product_ids, ))
        # -----------------------------------------------------
        # Above will help in creating a SAFE SQL string compared
        # to using format()
        # Additionally fields can be taken as parameter so in case
        # of any future change in the required fields, query need
        # not be changed but the fields can be appended, replaced
        # as per the requirement
        # Final query should look as follows,
        # -----------------------------------------------------
        #  query = "SELECT 
        #       %(query_fields)s
        #       FROM product 
        #       WHERE product_id IN %(product_ids)s"
        # query_fields = 'product_id, product_manual_data'
        # product_ids = tuple(ids)
        # cursor.execute(query, (query_fields, product_ids))
        # -----------------------------------------------------
        cursor.execute('''
            SELECT product_id, product_manual_data
            FROM product
            WHERE product_id IN {}
        '''.format(tuple(ids)))
        
        # Cursor can be closed after fetching the values from it in
        # a variable.
        # -----------------------------------------------------
        # product_data = cursor.fetchall()
        # cursor.close()
        # return product_data
        # -----------------------------------------------------
        return cursor.fetchall()

        # Above piece can be written using 'with' keyword to avoid 
        # writing cursor.close().
        # So as part of the db module, we can create a small cursor
        # class that has the cursor object. Cursor implements __entry__ 
        # for acquiring a cursor from the connection and whenever with 
        # block ends __exit__() cleans up the cursor, which in turn helps
        # preventing any side-effects from using an stale cursor.


# Avoid using global variable, can be converted to function
# which returns returns generator object from pathlib.Path()
# Additionally, as we have a clear intent for pdf files, we 
# can tweak expression in glob to '*.pdf'.
# Above will help in removing the complete for loop to find
# pdf files from the given the path using 'endswith()'
# -----------------------------------------------------------
# def get_pdf_file_path(base_path='/var/lib/app'):
#   return pathlib.Path(base_path).glob('*.pdf')
# 
# for p in get_pdf_file_path():
#   ...
# -----------------------------------------------------------

tmp = pathlib.Path('/var/lib/app').glob('*')
plist = []
for p in tmp:
    if p.name.endswith('pdf'):
        plist.insert(0, p)
del tmp

def render_product_manual(data):
    d = json.loads(data)
    # To be over precautious we can go ahead and check for the
    # KeyError we expect the data to have a key 'manual_filename'
    # which does raises an error by default but we can explicitly
    # do it to be respectful of The Zen of python :)
    # ----------------------------------------------------------
    # if 'manual_filename' not in d:
    #   raise KeyError('nice message indicating the error')
    # elif not d['manual_filename']:
    #   raise ValueError('Product details have no manual')
    # ----------------------------------------------------------
    if not d['manual_filename']:
        raise ValueError('Product details have no manual')

    # As this loop tries to check whether the given manual file
    # exists on the given path, loop can be terminated whenever
    # we find the first entry for the file, provided we are not
    # expecting multiple manuals with same file name in the given
    # location and we want to utilize the last one.
    # ----------------------------------------------------------
    # # For a unique entry of product manual in the given path
    # for p in plist:
    #   if d['manual_filename'] == p:
    #       break
    # else:
    #   raise ValueError('Product PDF is not found')
    # ----------------------------------------------------------
    # For multiple entry expectations approach taken below is well
    # fit for the purpose

    found_pdf = False

    # Refer to the comment from line 110 - 113
    for p in plist:
        if d['manual_filename'] == p:
            found_pdf = True
    if not found_pdf:
        raise ValueError('Product PDF is not found')

    # Since we are using shell directly to execute the command
    # it is prone to have shell injection. To prevent shell
    # injection we need to replace os.system() with subprocess.check_output()
    # with `shell=False`
    # We need to use absolute path to convert binary, better in terms of
    # operational ability as we can update the path to binary to check or
    # experiment with newer releases
    # -------------------------------------------------------------
    # import subprocess
    #
    # Not using a default value because if 'manual_render_params' is None
    # d.get() won't use the default value
    # if not d.get('manual_render_params'):
    #   render_params = ''
    # else:
    #   render_params = d.get('manual_render_params')
    # 
    # pdf_filename = d.get('manual_filename')
    # out_image_path = os.path.join('/tmp', 'tmp_image.jpg')
    # convert_exec_path = os.path.join('/usr', 'bin', 'convert')
    # 
    # In case we are using Python 3.5+, use f-strings
    # cmd = f"{convert_exec_path} {render_params} {pdf_filename} {out_image_path}"
    #
    # # For python 2 compatible,
    # # cmd = '%(convert_exec_path) %(render_params)s %(pdf_filename) %(out_image_path)' % {
    # #  "convert_exec_path": convert_exec_path,    
    # #  "render_params": render_params,
    # #  "pdf_filename": pdf_filename,
    # #  "out_image_path": out_image_path
    # # }
    #
    # cmd = cmd.split()
    # try:
    #   subprocess.check_output(cmd, shell=False)
    # except subprocess.CalledProcessError as err:
    #   raise err
    # ---------------------------------------------------------

    os.system('convert {} {} /tmp/tmp_image.jpg'.format(
        d.get('manual_render_params', ''), d['manual_filename']))

    # Returning an appropriate outcome to the caller in case of
    # an expection is better than just returning None.
    # Though function with no return will always return None.
    # It is better for caller to understand what failed to course
    # correct while debugging the program or utilizing function
    # in his piece of code
    # We can capture more generic exception in the except block
    # or we can use a custom exception.
    # ---------------------------------------------------------
    # try:
    #   return open('/tmp/tmp_image.jpg', 'rb')
    # except (IOError, OSError) as err:
    #   return (-1) # or some appropriate value to the caller
    # ---------------------------------------------------------
    try:
        return open('/tmp/tmp_image.jpg', 'rb')
    except:
        pass