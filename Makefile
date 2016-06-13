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

fetchWind:
	# TODO: FETCH LAST 6 hour fcast instead of 0hrs
	# &subregion=&leftlon=0&rightlon=360&toplat=90&bottomlat=-90
	# See other variables (clouds?) at
	# http://www.nco.ncep.noaa.gov/pmb/docs/on388/table2.html
	# and http://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p50.pl?dir=%2Fgfs.2016061000
	# *** USE 0.25 deg hourly (!) for wind !! ***
	# and http://www.ftp.ncep.noaa.gov/data/nccf/com/gfs/prod/gfs.2016061000/gfs.t00z.sfluxgrbf00.grib2
	# for solar
	curl "http://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p50.pl?file=gfs.t00z.pgrb2full.0p50.f000&lev_10_m_above_ground=on&var_UGRD=on&var_VGRD=on&var_DLWRF=on&var_DSWRF=on&dir=%2Fgfs.`date '+%Y%m%d'`00" -o gfs.t00z.pgrb2.0p50.f000
	JAVA_HOME="`/usr/libexec/java_home -v 1.8`" java -Xmx512M -jar grib2json/target/grib2json-0.8.0-SNAPSHOT/lib/grib2json-0.8.0-SNAPSHOT.jar \
		-d -n -o backend/data/gfs.json gfs.t00z.pgrb2full.0p50.f000
	rm gfs.t00z.pgrb2full.0p50.f000

fetchSolar:
	curl "http://nomads.ncep.noaa.gov/cgi-bin/filter_cfs_flx.pl?file=flxf`date '+%Y%m%d'`00.01.`date '+%Y%m%d'`00.grb2&lev_surface=on&var_DLWRF=on&var_DSWRF=on&leftlon=0&rightlon=360&toplat=90&bottomlat=-90&dir=%2Fcfs.`date '+%Y%m%d'`%2F00%2F6hrly_grib_01" -o solar.grb2

db:
	mongod
