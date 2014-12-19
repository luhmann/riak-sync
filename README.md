Introduction
============

The first script (parseImages) takes all the keys conforming to a certain pattern from a redis and parses their content for a
configurable number of key-names that contain image-paths on an riak-instance. These are used to generate
a pickle-file that contains a deserializable python list. 

The second script (syncImages) takes this python list and turns it into a set to ensure that duplicates are eliminated. 
It then checks each image if it exists on the target riak in the bucket 'ez' and if not looks into the dumped ez, assets
for it. The approach to determine the correct image is to match the filename of the local file against the second part
of the image-filename within the riak. It then calculates the adler32-hash as it would have been created by ez and 
compares it with the adler32-hash that is the first part of the riak-filename. (Adler32 has a higher probability of
collisions, that means that this is not foolproof!).

If it finds a match it encodes the local image-file and pushes it into the targeted riak


Install system dependencies:

`brew install python libmagic libtiff libjpeg webp little-cms2`

Install python packages:

`pip install -r requirements.txt`


### Get the redis keys:

Sync the complete live redis to your local host or devbox. You can use the redis-sync-sync script for this:

- `git clone git@github.com:luhmann/redis-sync.git`

- In the cloned folder: `python redisSync.py --redisSrc="<the redis master>" --redisDest="<your dev-box"`

### Get the ezpublish-assets
- Create a folder 'ez-data' one level up from where this repo lies on your local disk

- Start the Jenkins Job for the EZ-Db-Sync (http://jenkins-server/jenkins/view/Feature-Based%20Deployment/view/FBD%20-%20CMS/job/CMS%20-%20ezPublish%20DB%20Sync/)

- DO NOT promote it, your only after the dumped assets

- Copy the assets.tbz2 file to the 'ez-data' directory. You can either try doing this by clicking the file in jenkins, 
which was not that reliable during testing, or get via scp. The folder on jenkins is (currently) /var/lib/jenkins/jobs/CMS\ -\ ezPublish\ DB\ Sync/workspace/assets.tbz2

- Unpack the folder within the ez-data-directory an folder called 'assets' should be created. It is what the script expects.

### Parse the image from the redis content

The files are not parameterized to take arguments yet, so open `parseImages.py` and change the line:

> redisHandle = redis.StrictRedis(host='frontend.vag-jfd.magic-technik.de', port=6379, db=0)

to point to the host you dumped the redis-keys in step1 to

Execute: `python parseImages.py`

A file called images.txt should be generated and it should be well filled, at the point of writing the live-page
contained close to 46000 references to images


### Sync the images to the riaks

Open `syncImages.py` and check that `riakClientLive` points to the correct target machine. And that it is referenced
in the `riakClient`-variable.

Execute: `python syncImages.py`

You will get a direct output of everything the script does. The images that where actually uploaded will be piped
into `upload.log`, errors are logged in `error.log`