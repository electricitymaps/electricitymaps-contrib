FROM python:2.7
ADD . /home/
WORKDIR /home/
# Install pygrib dependencies manually
RUN apt-get update && apt-get install -y libgrib-api-dev && pip install numpy==1.10.1 pyproj==1.9.4
RUN make install
CMD make server
