Requires docker build (from project folder / parent repository)
```
docker-compose build public_web 
```

To build js:
```
./build.sh
```

when installing for first time, run
```
npm install
cordova prepare
```

To build cordova:
```
cordova build {ios,android}
```

To run:
```
cordova run {ios,android}
```

To do a release build (android):
```
cordova build android --release -- --keystore=electricitymap.keystore --alias=electricitymapkey
```

To do a release build (ios):
```
cordova build ios --release
```

To push a new release:
```
code-push release-cordova electricitymap-{ios,android} {ios,android}
code-push promote electricitymap-{ios,android} Staging Production
```

Note about releases: bumping the release number will cause a new binary to be created. All code-push updates are tied to a binary version, meaning that apps will only update to code-push updates that are compatible with their binary version.

## Troubleshooting

If you get

```
ld: warning: directory not found for option '-L/Users/oliviercorradi/Library/Developer/Xcode/DerivedData/electricityMap-bodzannsraziqncaeafoyayssnvd/Build/Products/Debug-iphonesimulator/GoogleToolboxForMac'
ld: warning: directory not found for option '-L/Users/oliviercorradi/Library/Developer/Xcode/DerivedData/electricityMap-bodzannsraziqncaeafoyayssnvd/Build/Products/Debug-iphonesimulator/nanopb'
ld: library not found for -lGoogleToolboxForMac
```

while building for ios, you should run `pod install` from the `platforms/ios` directory.
