`drawer_local.py` is for drawing where files are locally stored on the computer.\
`drawer.py` is for drawing where files are stored in Google Drive.\

### For storing images on Google Drive
Make sure folder access permission is set to viewer.\
Make sure credentials.json is in the current directory.\

### configurations in drawer.py
```bash
IMG_FOLDER_ID = "<folder id of images with metadata>"
ANNOTATED_IMG_FOLDER_ID = "<folder id of annotated images>"
```

### build Docker image
```bash
docker build -t drawer . && docker builder prune -f
```

### run container
```bash
docker run [OPTIONS] IMAGE [COMMAND] [ARG...]
```

### if you stored your geotagged frames and annotated frames locally on your laptop
```bash
docker run -it -p 5001:5000 drawer\
    -v <absolute path to geotagged-images folder>:/app/geotagged_images\ 
    -v <absolute path to annotated-images folder>:/app/annotated_images\
```

### if you stored your geotagged frames and annotated frames on Google Drive
```bash
docker run -it -p 5001:5000
```

### to clear all Docker builds and images
```bash
docker system prune -a --volumes -f
```

### QGIS setup
In QGIS, add the code provided in code_qgis.txt into Display tag of the Density Map Layer and click apply.