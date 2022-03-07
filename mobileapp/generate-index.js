var ejs = require("ejs");
var fs = require("fs");

const STATIC_PATH = "www/electricitymap";

const {
  localeToFacebookLocale,
  supportedFacebookLocales,
  languageNames,
} = require("./locales-config.json");

const locales = Object.keys(languageNames);
const localeConfigs = {};
localeConfigs['en'] = require(`${__dirname}/locales/en.json`);
// duplicated from server.js
// * Long-term caching
function getHash(key, ext, obj) {
  let filename;
  if (typeof obj.assetsByChunkName[key] == "string") {
    filename = obj.assetsByChunkName[key];
  } else {
    // assume list
    filename = obj.assetsByChunkName[key].filter((d) =>
      d.match(new RegExp("." + ext + "$"))
    )[0];
  }
  return filename.replace("." + ext, "").replace(key + ".", "");
}

const template = ejs.compile(
  fs.readFileSync("../web/views/pages/index.ejs", "utf8")
);
const manifest = JSON.parse(
  fs.readFileSync(`${STATIC_PATH}/dist/manifest.json`)
);

const html = template({
  maintitle: localeConfigs["en"].misc.maintitle,
  alternateUrls: [],
  bundleHash: getHash("bundle", "js", manifest),
  vendorHash: getHash("vendor", "js", manifest),
  stylesHash: getHash("styles", "css", manifest),
  vendorStylesHash: getHash("vendor", "css", manifest),
  // Keep using relative resource paths on mobile platforms as that's
  // the way to keep them working with file:// protocol and HashHistory
  // doesn't require paths to be absolute.
  resolvePath: (relativePath) => relativePath,
  isCordova: true,
  FBLocale: localeToFacebookLocale["en"],
  supportedLocales: locales,
  supportedFBLocales: supportedFacebookLocales,

  //<meta http-equiv="Content-Security-Policy" content="default-src * 'self' 'unsafe-inline' data: gap://ready https://ssl.gstatic.com 'unsafe-eval' blob:; style-src * 'unsafe-inline'; media-src *;" />
});

fs.writeFileSync("www/electricitymap/index.html", html);
