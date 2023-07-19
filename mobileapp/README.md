# Electricity Maps Mobile Apps

This is a capacitor project that builds the mobile apps from the web directory

## Prerequisites

- Follow this guide: https://capacitorjs.com/docs/getting-started/environment-setup (but skip the Android SDK part)
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

## Development

If you have the web app installed and running and want to do production builds,the following commands will run everything you need.

Navigate to mobileapp and run:

`pnpm build-ios`
`pnpm build-android`

**Did the above not work?**

<details>

  <summary><b>Guide to manually run the same step</b></summary>

1. First make sure you have installed and built the web app.

   - Navigate to the **web** directory then:
     - `pnpm install`
     - `pnpm build`

2. To enable hot reload you must runt the web app locally on port 5173: `pnpm dev`

3. Navigate to the **mobileapp** directory and run `pnpm install`

4. Add Android and iOS to Capacitor:

   - `pnpm exec cap add android`
   - `pnpm exec cap add ios`

5. Copy Assets to app directories: `pnpm exec cap copy`

6. Sync the web project to capacitor: `pnpm exec cap sync`

</details>

### Run the app locally with hot reload

```bash
pnpm dev-android
pnpm dev-ios
```

## Deployment

We use [fastlane](https://fastlane.tools/) to build and deploy the apps automatically.
See [fastlane/README.md](./fastlane/README.md) for more information.

### Setup

1. `bundle install`
2. Ensure you have the following keyfiles locally (ask the team internally to get them):
   - `.env.default`
   - `android/electricitymap.keystore`
   - `android/keystore.properties`
   - `fastlane/fastlane-key.json`
3. Update keys in `.env.default`:
   - Add your own Apple ID
   - Open https://appleid.apple.com/account/manage and create an App-Specific Password to be used for the FASTLANE_APPLE_APPLICATION_SPECIFIC_PASSWORD environment variable
   - Ask internally for the team ids

### Making a beta build

Makes a build and distributes it for internal testing.

```bash
pnpm run fast android beta
pnpm run fast ios beta
```

### Publishing to the app stores

Once beta builds have been tested and approved, you can publish them to the app stores.

```bash
pnpm run fast ios publish
pnpm run fast android publish
```

---

If you need more information:
https://capacitorjs.com/docs/getting-started

## Troubleshooting

<details>
  <summary>Android emulator not working?</summary>

Android studio will need a virtual device, shown here in the Android Studio opening screen:
![](./VDM.png)

If you get XCode error "Command PhaseScriptExecution failed with a nonzero exit code"
Then in Pods-Electricity Maps-frameworks.sh
Replace:
`source="$(readlink "${source}")"`
With:
`source="$(readlink -f "${source}")"`

</details>
