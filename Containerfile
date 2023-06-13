<<<<<<< Updated upstream
FROM ghcr.io/clamsproject/clams-python-opencv4:1.0.2
=======
# Use the same base image version as the clams-python python library version
FROM ghcr.io/clamsproject/clams-python:1.0.2
# See https://github.com/orgs/clamsproject/packages?tab=packages&q=clams-python for more base images
# IF you want to automatically publish this image to the clamsproject organization, 
# 1. you should have generated this template without --no-github-actions flag
# 1. to add arm64 support, change relevant line in .github/workflows/container.yml 
#     * NOTE that a lots of software doesn't install/compile or run on arm64 architecture out of the box 
#     * make sure you locally test the compatibility of all software dependencies before using arm64 support 
# 1. use a git tag to trigger the github action. You need to use git tag to properly set app version anyway

>>>>>>> Stashed changes
################################################################################
# DO NOT EDIT THIS SECTION
ARG CLAMS_APP_VERSION
ENV CLAMS_APP_VERSION ${CLAMS_APP_VERSION}
################################################################################

################################################################################
# clams-python base images are based on debian distro
# install more system packages as needed using the apt manager
<<<<<<< Updated upstream
RUN apt-get update && apt-get install -y build-essential cmake \
    wget git unzip

# lib for tesseract
RUN apt-get -y install \
        g++ \
        autoconf \
        automake \
        libtool \
        autoconf-archive \
        zlib1g-dev \
        libicu-dev \
        libpango1.0-dev \
        libcairo2-dev

# tesseract 4
RUN apt-get install -y libleptonica-dev \
    libtesseract4 \
    libtesseract-dev \
    tesseract-ocr

# Get language data.
RUN apt-get install -y \
    tesseract-ocr-eng
    # add more if needed
    
#RUN apt-get -y clean all && \
#    rm -rf /var/lib/apt/lists/* && \
#
#    # Clean
#    apt-get -y remove \
#        python3-dev \
#        libatlas-base-dev \
#        gfortran \
#        libgtk2.0-dev \
#        libavcodec-dev \
#        libavformat-dev \
#        libswscale-dev \
#        libjpeg-dev \
#        libpng-dev \
#        libtiff-dev \
#        libv4l-dev
#        && \
#    apt-get clean && \
#    rm -rf /opencv /opencv_contrib /var/lib/apt/lists/*
=======
>>>>>>> Stashed changes
################################################################################

################################################################################
# main app installation
COPY ./ /app
WORKDIR /app
RUN pip3 install -r requirements.txt

# default command to run the CLAMS app in a production server 
CMD ["python3", "app.py", "--production"]
################################################################################
