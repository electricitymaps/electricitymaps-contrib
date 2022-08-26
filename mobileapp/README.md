# Mobileapp

## Prerequisites

A lot of things here, so keep your tongue in your mouth and frequently use `cordova requirements` to verify changes. You might also have to restart your terminal in between steps.

### iOS

- install Xcode
- `brew install cocoapods`

### Android

- install JDK v8 <-- to avoid having to create an Oracle account(!), you can find a `jdk-8u321-macosx-x64.dmg` in our internal Google Drive.
- `brew install gradle`
- install Android Studio - make sure you open it and go through the install wizard in the start
  - Also go to Tools > SDK Manager and install SDK v29
- Follow the steps here: https://www.brainfever.co.uk/2022/02/04/build-tool-32-1-0-rc1-is-missing-dx-at/
  - instead of last step, add the following to your `.zshrc` file:
  ```bash
    export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk1.8.0_321.jdk/Contents/Home
    export PATH=$JAVA_HOME/bin:$PATH
    export PATH=$PATH:/Library/Android/sdk/platform-tools
    export PATH=$PATH:/Library/Android/sdk/tools
    export ANDROID_SDK_ROOT=~/Library/Android/sdk
    export ANDROID_HOME=~/Library/Android/sdk
  ```

See also the [guide in documentation](https://cordova.apache.org/docs/en/latest/guide/platforms/android/index.html#setting-environment-variables) for details and links.

### General

- Run `npm install -g cordova@10.0.0 code-push-cli@2.1.9`
- Run `npm install`
- Download `GoogleService-Info.plist` and `google-services.json` from Firebase and add them to this folder

If you want your local JavaScript changes to be reflected, you need to disable Codepush by commenting out the `codePush.sync` calls in `../web/src/cordova.js`.

To build the JavaScript:

```bash
docker-compose build web && ./build.sh
```

If you want to access the public API you will need a token:

```bash
docker-compose build web --build-arg ELECTRICITYMAP_PUBLIC_TOKEN=... && ./build.sh
```

## Building & running apps

To add the app to cordova

```bash
cordova platform add {ios,android}
```

To build the cordova app:

```bash
cordova build {ios,android}
```

To run the app:

```bash
cordova run {ios,android}
```

In case you want to use xcode:

```bash
open platforms/ios/electricityMap.xcworkspace
```

Note when building from XCode, one has to remember to run `cordova prepare ios` before each build. This will push the `www/` files into the iOS platform. Without this, the `www` files won't be updated.
This is not required when using `cordova build` (it automatically runs `cordova prepare`).

## Releasing a new (code-push) build

To do a release build (android):

```bash
cordova build android --release -- --keystore=electricitymap.keystore --alias=electricitymapkey --storePassword XXX --password XXX
```

(ask internally for the password)

To do a release build (ios):

```bash
cordova build ios --release
```

To push a new cordova release:

```bash
# You need to first login and create an account at appcenter.ms - and perhaps also get invited to the organization
code-push login

code-push release-cordova electricitymap-{ios,android} {ios,android}
code-push promote electricitymap-{ios,android} Staging Production
```

## Release a new app-store build

Note about releases: bumping the release number will cause a new binary to be created. All code-push updates are tied to a binary version, meaning that apps will only update to code-push updates that are compatible with their binary version.

To push a new store release:

- Update the version in config.xml
- Run `cordova prepare` if you're planning to build directly from XCode
- Make release builds (previously explained)
- iOS
  - Make sure you have XCode installed and are signed in under preferences > accounts
  - Go to [appstoreconnect.apple.com](https://appstoreconnect.apple.com) and create a new version (blue + icon in the left panel)
  - Follow [this guide](https://jackmckew.dev/releasing-cordova-apps-on-google-play-app-store.html)
  - Go into TestFlight and test on your own device
  - Submit the new build for review when everything is looking good
- Android
  - Open folder `mobileapp/platforms/android/app/build/outputs/apk/release` and upload the `app-release.apk` file on [Play Store Console](https://play.google.com/console)
- Celebrate!

## App/Play Store Release Checklist

- Run a debug build on iOS/Android and check that code-push properly installs an update.
- Check app icons - if it's a robot (Cordova logo), look into `platforms/ios/electricityMap/Images.xcassets/AppIcon.appiconset` and ensure that there's only emap icons. Otherwise delete them and rerun build.sh

## Troubleshooting

If you get

```
ld: warning: directory not found for option '-L/Users/oliviercorradi/Library/Developer/Xcode/DerivedData/electricityMap-bodzannsraziqncaeafoyayssnvd/Build/Products/Debug-iphonesimulator/GoogleToolboxForMac'
ld: warning: directory not found for option '-L/Users/oliviercorradi/Library/Developer/Xcode/DerivedData/electricityMap-bodzannsraziqncaeafoyayssnvd/Build/Products/Debug-iphonesimulator/nanopb'
ld: library not found for -lGoogleToolboxForMac
```

while building for ios, you should run `pod install` from the `platforms/ios` directory.

If you get a blank screen on iOS, as https://github.com/Microsoft/cordova-plugin-code-push/issues/434 hardcodes the cordova-plugin-file version, you must:

```bash
cordova plugin rm cordova-plugin-file --force
cordova plugin rm cordova-plugin-file-transfer --force
cordova plugin add cordova-plugin-file@latest
cordova plugin add cordova-plugin-file-transfer@latest
```

If the Android icons are not working, check the AndroidManifest.xml and double check that the key "@mipmap/ic_launcher" is correctly set (and not @mipmap/icon)

If you get "No known instance method for selector 'userAgent' in CDVFileTransfer.m", then follow information from https://github.com/apache/cordova-plugin-file-transfer/issues/258#issuecomment-956233758

If you get "env: node: No such file or directory", then it means you don't have node set up at /usr/local/bin/node (you might be using nvm).
This will create a symlink from /usr/local/bin/node to your current node version:

```bash
ln -s $(eval which node) /usr/local/bin/node
```

### Cannot find module '../../src/plugman/platforms/ios'

(From https://github.com/nordnet/cordova-universal-links-plugin/issues/131#issuecomment-387761895)

In plugins\cordova-universal-links-plugin\hooks\lib\ios\xcodePreferences.js

Change line 135-150:

```javascript
function loadProjectFile() {
  var platform_ios;
  var projectFile;

  try {
    // try pre-5.0 cordova structure
    platform_ios = context.requireCordovaModule(
      'cordova-lib/src/plugman/platforms'
    )['ios'];
    projectFile = platform_ios.parseProjectFile(iosPlatformPath());
  } catch (e) {
    // let's try cordova 5.0 structure
    platform_ios = context.requireCordovaModule(
      'cordova-lib/src/plugman/platforms/ios'
    );
    projectFile = platform_ios.parseProjectFile(iosPlatformPath());
  }

  return projectFile;
}
```

To this:

```javascript
function loadProjectFile() {
  var platform_ios;
  var projectFile;
  try {
    // try pre-5.0 cordova structure
    platform_ios = context.requireCordovaModule(
      'cordova-lib/src/plugman/platforms'
    )['ios'];
    projectFile = platform_ios.parseProjectFile(iosPlatformPath());
  } catch (e) {
    try {
      // let's try cordova 5.0 structure
      platform_ios = context.requireCordovaModule(
        'cordova-lib/src/plugman/platforms/ios'
      );
      projectFile = platform_ios.parse(iosPlatformPath());
    } catch (e) {
      // try cordova 7.0 structure
      var iosPlatformApi = require(path.join(
        iosPlatformPath(),
        '/cordova/Api'
      ));
      var projectFileApi = require(path.join(
        iosPlatformPath(),
        '/cordova/lib/projectFile.js'
      ));
      var locations = new iosPlatformApi().locations;
      projectFile = projectFileApi.parse(locations);
    }
  }
  return projectFile;
}
```

### Cannot read property 'manifest' of undefined

(From https://stackoverflow.com/a/57638582/11940257)

Go to file `plugins/cordova-universal-links-plugin/hooks/lib/android/manifestWriter.js` and change the following:

```javascript
var pathToManifest = path.join(
  cordovaContext.opts.projectRoot,
  'platforms',
  'android',
  'cordovaLib',
  'AndroidManifest.xml'
);
```

to

```javascript
var pathToManifest = path.join(
  cordovaContext.opts.projectRoot,
  'platforms',
  'android',
  'app',
  'src',
  'main',
  'AndroidManifest.xml'
);
```
