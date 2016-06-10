.PHONY: server

install:
	pip install -r server/requirements.txt
	sudo gem install foreman
	
install-grib2json:
	git clone https://github.com/cambecc/grib2json
	cd grib2json && mvn package && tar -xvf target/grib2json-0.8.0-SNAPSHOT.tar.gz

server:
	foreman start

api:
	python -u server/server.py

feeder:
	python -u server/feeder.py

fetchWind:
	# TODO: FETCH LAST 6 hour fcast instead of 0hrs
	# &subregion=&leftlon=0&rightlon=360&toplat=90&bottomlat=-90
	# See other variables (clouds?) at
	# http://www.nco.ncep.noaa.gov/pmb/docs/on388/table2.html
	# and http://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_1p00.pl?dir=%2Fgfs.2016061000
	curl "http://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_1p00.pl?file=gfs.t00z.pgrb2.1p00.f000&lev_10_m_above_ground=on&var_UGRD=on&var_VGRD=on&var_DSWRF=on&var_DLWRF&dir=%2Fgfs.`date '+%Y%m%d'`00" -o gfs.t00z.pgrb2.1p00.f000
	JAVA_HOME="`/usr/libexec/java_home -v 1.8`" java -Xmx512M -jar grib2json/target/grib2json-0.8.0-SNAPSHOT/lib/grib2json-0.8.0-SNAPSHOT.jar \
		-d -n -o server/data/gfs.json gfs.t00z.pgrb2.1p00.f000
	rm gfs.t00z.pgrb2.1p00.f000

db:
	mongod
