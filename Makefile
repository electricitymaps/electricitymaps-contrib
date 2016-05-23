install:
	pip install -r server/requirements.txt
	sudo gem install foreman

server:
	foreman start

api:
	python server/server.py

feeder:
	python server/feeder.py

db:
	mongod
