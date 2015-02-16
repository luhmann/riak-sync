import os
import pickle
import string
import fnmatch
import zlib
import scandir
import base64
import magic
import json
import StringIO
import time
import logging
import sys
from PIL import Image
from riak import RiakClient
from time import strftime


baseDir = os.path.dirname(os.path.realpath(__file__))
srcFile = os.path.join(baseDir, 'images.txt')
assetDir = os.path.realpath(os.path.join(baseDir, '..', 'ez-data', 'assets'))
uploadFileDir = os.path.join(baseDir, 'filesToUpload')
serverMediaDirPrefix = 'var/ezflow_site/storage/images'
riakClientLive = RiakClient(protocol='http', host='vm-riak-03.lve-1.magic-technik.de', http_port=8098)
riakClientDevBox = RiakClient(protocol='pbc', host='frontend.beta.magic-technik.de', http_port=8087)

riakClient = riakClientLive
riakBucket = riakClient.bucket('ez')

logger = logging.getLogger('error_logger')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(os.path.join(baseDir, 'error.log'))
fh.setLevel(logging.WARNING)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
expanded_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(expanded_formatter)
logger.addHandler(fh)
logger.addHandler(ch)

uploadLogger = logging.getLogger('upload_logger')
uploadLogger.setLevel(logging.DEBUG)
fhu = logging.FileHandler(os.path.join(baseDir, 'upload.log'))
fhu.setLevel(logging.INFO)
uformatter = logging.Formatter('%(message)s')
fhu.setFormatter(uformatter)
uploadLogger.addHandler(fhu)



def parse_filename(riak_key):
    # print riak_key
    parts = string.split(riak_key, '-')
    adler = parts[0]
    del parts[0]

    return {
        'adler' : adler,
        'filename' : '-'.join(parts)
    }

def find_file(image):
    matches = []
    for root, dirnames, filenames in scandir.walk(assetDir):
        for filename in fnmatch.filter(filenames, image):
            matches.append(os.path.join(root, filename))

    return matches

def img_exists(riak_key):
    obj = riakBucket.get(riak_key)

    return obj.exists


def calc_adler_hash_file(file):

    relative = file.replace(assetDir, '')
    # print relative

    hashPath = serverMediaDirPrefix + relative

    # print hashPath

    calcAdler = hex(zlib.adler32(hashPath) & 0xffffffff)[2:]

    if len(calcAdler) == 7:
        calcAdler = str(0) + calcAdler

    return calcAdler

def find_correct_file(matches, adlerHash):
    for match in matches:
        calcAdler = calc_adler_hash_file(match)

        if (calcAdler == adlerHash):
            return match
        else:
            continue

    return None

def get_basepath(filepath):
    return os.path.splitext(filepath)[0]

def create_img_json(img_path):
    if not os.path.isfile(img_path):
        logger.info('Not a valid image file %s' % img_path)
        return None

    im = Image.open(img_path)
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(img_path)
    output = StringIO.StringIO()
    im.save(output, im.format   )
    json_repr = {
        'id': os.path.basename(img_path),
        'title': os.path.basename(img_path),
        'size': str(os.path.getsize(img_path)),
        'width': str(im.size[0]),
        'height': str(im.size[1]),
        'mimeType': mime_type,
        'imageBinary': base64.b64encode(output.getvalue()),
        'type': 'image',
        'origin': 'Python ImageSync',
        'createdAt': str(int(time.time()))
    }
    output.close()

    return json.dumps(json_repr)


def save_to_riak(key, json):
    logger.info('Uploading %s' % key)
    uploadLogger.info(key)
    img = riakBucket.new(key, encoded_data=json)
    img.store()

def save_to_disk(key, data):
    with open(os.path.join(uploadFileDir, key), 'w') as outfile:
        json.dump(data, outfile)


def main():
    logger.info('Started run at %s' % strftime("%Y-%m-%d %H:%M:%S"))
    logger.debug('Asset-Dir: %s' % assetDir)

    imageList = pickle.load(open(srcFile, 'rb'))

    logger.info('Images with duplicates %s' % len(imageList))

    imageList = set(imageList)

    logger.info('Unique Images %s' % len(imageList))


    for img in imageList:
        logger.info('------------------------------------------------')
        logger.info(img)

        if img_exists(img) is True:
            logger.info('Found %s in riak' % img)
            continue

        details = parse_filename(img)
        logger.info(details)

        matches = find_file(details['filename'])

        if len(matches) > 1:
            file = find_correct_file(matches, details['adler'])
        elif len(matches) is 1:
            file = matches[0]
        else:
            logger.error('Error could not find match for %s' % img)
            continue

        if file is None:
            logger.error('Error could not find match for %s' % img)
            continue


        calcAdler = calc_adler_hash_file(file)

        if calcAdler != details['adler']:
            logger.warning('Error could not match hashes of %s' % img)
            continue

        imgJson = create_img_json(file)

        # print imgJson
        # save_to_disk(img, imgJson)
        save_to_riak(img, imgJson)

        logger.debug('PHP Adler Hash %s' % details['adler'])
        logger.debug('Python Adler Hash %s' % calcAdler)

    logger.info('Run completed at %s' % strftime("%Y-%m-%d %H:%M:%S"))

main()