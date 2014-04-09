import redis
import os
import requests
import json
from riak import RiakClient, RiakNode

redisKeyHandle = None
redisHandle = redis.StrictRedis(host='frontend.dev-fe-01.vag-jfd.magic-technik.de', port=6379, db=0)
redisKeyPrefix = 'content:v1:de:de:live:'
baseDir = os.path.dirname(os.path.realpath(__file__))
imageKeys = ['src', 'image', 'thumbnail', 'cover']

def readRedisKeys():
    keyListFilename = os.path.join(baseDir, 'keys.txt')
    #keys = tuple(open(keyListFilename, 'r'))
    return  [line.strip() for line in open(keyListFilename, 'r')]


def find_values(id, json_repr):
    results = []

    def _decode_dict(a_dict):
        try: results.append(a_dict[id][3:])
        except KeyError: pass
        return a_dict

    obj = json.loads(json_repr, object_hook=_decode_dict) # return value ignored
    return results

def getImgUrls(pages):
    imgList = []

    for page in pages:
        content = redisHandle.get(redisKeyPrefix + page)

        for key in imageKeys:
            imgList = imgList + find_values(key, content)

    return imgList

def saveImage(riakObj, filename):
    with open(os.path.join(baseDir, filename), 'w+') as f:
        f.write(riakObj.encoded_data)


pages = readRedisKeys()
print 'Redis Keys: \n' + '\n'.join(pages)

imgUrls = getImgUrls(pages)

print 'Found ' + str(len(imgUrls)) + ' referenced images \n'

rcLive = RiakClient(protocol='http', host='10.228.39.181', http_port=8098)
rbLive = rcLive.bucket('ez')

rcInt = RiakClient(protocol='http', host='int-riak-01.magic-technik.de', http_port=8098)
rbInt = rcInt.bucket('ez')

def saveToIntRiak(key, riakObj):
    img = rbInt.new(key, encoded_data=riakObj.encoded_data, content_type=riakObj.content_type)
    img.store()

for img in imgUrls:
    print img
    buffer = rbLive.get(img)
    saveToIntRiak(img, buffer)











#print redisHandle.get(redisKeyPrefix + '/');