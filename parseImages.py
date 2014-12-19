import redis
import json
import os
import pickle

redisHandle = redis.StrictRedis(host='frontend.vag-jfd.magic-technik.de', port=6379, db=0)
redisKeyPrefix = 'content:v1:de:de:live:'
imageKeys = ['src', 'image', 'thumbnail', 'cover']

redisKeyPrefixBuzz = 'buzz:v1:de:de:live:'

baseDir = os.path.dirname(os.path.realpath(__file__))
allLiveImgUrls = []

def getImgUrls(redisKey):
    imgList = []

    content = redisHandle.get(redisKey)
    # print content

    for key in imageKeys:
        imgList = imgList + find_values(key, content)


    return imgList

def find_values(id, json_repr):
    results = []

    def _decode_dict(a_dict):
        try:
            if isinstance(a_dict[id], basestring):
                results.append(a_dict[id][3:])
        except KeyError: pass
        return a_dict

    obj = json.loads(json_repr, object_hook=_decode_dict) # return value ignored
    return results

def save_file(filename, content):
    with open(os.path.join(baseDir, filename), 'a') as the_file:
        the_file.write('\n'.join(content))


keys = redisHandle.keys('*')

for key in keys:
    print key

    if not str(key).startswith(redisKeyPrefix):
        continue

    allLiveImgUrls = allLiveImgUrls + getImgUrls(key)

pickle.dump(allLiveImgUrls, open(os.path.join(baseDir, 'images.txt'), 'wb'))