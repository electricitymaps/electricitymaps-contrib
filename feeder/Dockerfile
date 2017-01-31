FROM python:2.7
# Install node
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash - && \
    apt-get install -y nodejs
# Install pygrib dependencies manually
RUN apt-get install -y libgrib-api-dev libsnappy-dev && \
    pip install numpy==1.10.1 pyproj==1.9.4
WORKDIR /home/feeder
# Only add requirements to enable cached builds when it is unchanged
ADD feeder/requirements.txt /home/feeder/requirements.txt
RUN pip install -r requirements.txt
# Same with package.json
ADD feeder/package.json /home/feeder/package.json
RUN npm install
# Add the rest
ADD feeder /home/feeder
ADD shared /home/shared
CMD python -u feeder.py
