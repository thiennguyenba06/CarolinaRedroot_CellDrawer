drawer_local.py is for drawing where files are locally stored on the computer
drawer.py is for drawing where files are stored in Google Drive

For storing images on Google Drive
Make sure folder access permission is set to viewer
Make sure credentials.json is in the current directory 
```bash
IMG_FOLDER_ID = "<folder id of images with metadata>"
ANNOTATED_IMG_FOLDER_ID = "<folder id of annotated images>"
```

```bash
# build Docker image
docker build -t drawer . && docker builder prune -f

# run container
docker run [OPTIONS] IMAGE [COMMAND] [ARG...]

# if you stored your geotagged frames and annotated frames locally on your laptop
docker run -it -p 5001:5000 drawer\
    -v <absolute path to geotagged-images folder>:/app/geotagged_images\ 
    -v <absolute path to annotated-images folder>:/app/annotated_images\

# if you stored your geotagged frames and annotated frames on Google Drive
docker run -it -p 5001:5000

# to clear all Docker builds and images
docker system prune -a --volumes -f
```