# Electricity Maps Mobile Apps

This is a capacitor project that builds the mobile apps from the web directory

## Prerequisites:

https://capacitorjs.com/docs/getting-started/environment-setup

Xcode

Android Studio

Homebrew

Node 18+




## First make sure you have installed and built the web app:

Navigate to the web directory then:

`pnpm install`

`pnpm build`

To enable hot reload you must runt he web app locally on port 5173:

`pnpm dev`

Navigate to the moibleapp directory then:

`pnpm install`


Add Android and iOS:

`pnpm exec cap add android`
`pnpm exec cap add ios`

Copy Assets to app directories:

`pnpm exec cap copy`

Sync the web project to capacitor:

`pnpm exec cap sync`

**Run the app locally with hot reload**

Android:

`pnpm dev-android`

iOS:

`pnpm dev-ios`



**Build app bundles**

App bundles are built through Android Studio and iOS
Android:

`pnpm exec open android`

iOS:

`pnpm exec open ios`



-------------------------------------------------------------------------------------



If you need more information:
https://capacitorjs.com/docs/getting-started



Android emulator not working?

Android studio will need a virtual device, shown here in the Android Studio opening screen:
![](./VDM.png)

