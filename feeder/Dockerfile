FROM java:8
WORKDIR /home/
ENV LANG=en_US.UTF-8
ENV PYTHONIOENCODING=utf8
RUN apt-get update
# Install python
RUN apt-get install -y gcc make python-dev libxml2-dev libxslt-dev gzip
RUN curl -s https://bootstrap.pypa.io/get-pip.py | python
# Install pygrib dependencies manually
RUN apt-get install -y maven
RUN apt-get install -y libgrib-api-dev && pip install numpy==1.10.1 pyproj==1.9.4
RUN git clone https://github.com/cambecc/grib2json && \
    cd grib2json && mvn package && tar -xvf target/grib2json-0.8.0-SNAPSHOT.tar.gz
# Install g++ for Cython required by panda
RUN apt-get install -y g++
# Only add requirements to enable cached builds when it is unchanged
ADD requirements.txt /home/requirements.txt
RUN pip install -r requirements.txt
# Add the rest
ADD . /home/
CMD python -u feeder.py
