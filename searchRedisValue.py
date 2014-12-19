import redis
import argparse

redisHandle = redis.StrictRedis(host='frontend.vag-jfd.magic-technik.de', port=6379, db=0)

parser = argparse.ArgumentParser()
parser.add_argument('--term', dest='searchTerm')
args = parser.parse_args()


keys = redisHandle.keys('*')
redisKeyPrefix = 'content:v1:de:de:live:'
redisKeyPrefixBuzz = 'buzz:v1:de:de:live:'
searchTerm = args.searchTerm

for key in keys:
    if not str(key).startswith(redisKeyPrefix):
        continue

    value = redisHandle.get(key)

    if searchTerm in value:
        print key