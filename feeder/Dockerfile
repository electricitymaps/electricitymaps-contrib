FROM python:2.7
WORKDIR /home/
RUN apt-get update
# Install python
# Install pygrib dependencies manually
RUN apt-get install -y libgrib-api-dev libsnappy-dev && \
    pip install numpy==1.10.1 pyproj==1.9.4
# Only add requirements to enable cached builds when it is unchanged
ADD requirements.txt /home/requirements.txt
RUN pip install -r requirements.txt
# Add the rest
ADD . /home/
CMD python -u feeder.py
