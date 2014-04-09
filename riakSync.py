import redis
import os
import requests
import json
from riak import RiakClient, RiakNode

redisHost = 'frontend.dev-fe-01.vag-jfd.magic-technik.de'
redisHandle = redis.StrictRedis(host=redisHost, port=6379, db=0)
redisKeyPrefix = 'content:v1:de:de:live:'
baseDir = os.path.dirname(os.path.realpath(__file__))
imageKeys = ['src', 'image', 'thumbnail', 'cover']

# Parses the keys.txt file and writes url
def readRedisKeys():
    keyListFilename = os.path.join(baseDir, 'keys.txt')
    return  [line.strip() for line in open(keyListFilename, 'r')]

# finds the values for keyname id in the json-structure
def find_values(id, json_repr):
    results = []

    def _decode_dict(a_dict):
        try: results.append(a_dict[id][3:])
        except KeyError: pass
        return a_dict

    obj = json.loads(json_repr, object_hook=_decode_dict) # return value ignored
    return results

# gets an array of image-urls from the redis values of the past page-urls
def getImgUrls(pages):
    imgList = []

    for page in pages:
        content = redisHandle.get(redisKeyPrefix + page)

        for key in imageKeys:
            imgList = imgList + find_values(key, content)

    return imgList

# unused helper method to save an image to the disk if you want that
def saveImage(riakObj, filename):
    with open(os.path.join(baseDir, filename), 'w+') as f:
        f.write(riakObj.encoded_data)


# Read in redis-keys
pages = readRedisKeys()
print 'Redis Keys: \n' + '\n'.join(pages)

# get all image-urls from those redis keys
imgUrls = getImgUrls(pages)

print 'Found ' + str(len(imgUrls)) + ' referenced images \n'

# connect to live riak
rcLive = RiakClient(protocol='http', host='10.228.39.181', http_port=8098)
rbLive = rcLive.bucket('ez')

# connect to integration riak
rcInt = RiakClient(protocol='http', host='int-riak-01.magic-technik.de', http_port=8098)
rbInt = rcInt.bucket('ez')

# save image in integration riak
def saveToIntRiak(key, riakObj):
    img = rbInt.new(key, encoded_data=riakObj.encoded_data, content_type=riakObj.content_type)
    img.store()

# get and save all images
for img in imgUrls:
    print img
    buffer = rbLive.get(img)
    saveToIntRiak(img, buffer)











#print redisHandle.get(redisKeyPrefix + '/');