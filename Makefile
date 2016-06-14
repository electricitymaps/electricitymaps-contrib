.PHONY: server

install:
	pip install -r backend/requirements.txt
	sudo gem install foreman
	
install-grib2json:
	git clone https://github.com/cambecc/grib2json
	cd grib2json && mvn package && tar -xvf target/grib2json-0.8.0-SNAPSHOT.tar.gz

server:
	foreman start

api:
	python -u backend/server.py

feeder:
	python -u backend/feeder.py

db:
	mongod
