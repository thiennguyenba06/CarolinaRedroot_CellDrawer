FROM python:3.12-bookworm

# Install system dependencies for OpenCV and Metadata processing
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx libglib2.0-0 libexiv2-dev g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Internal folders
# RUN mkdir -p geotagged_images annotated_images

# 
RUN chmod +x procedures.sh

EXPOSE 5000

# Start the program
CMD ["./procedures.sh"]