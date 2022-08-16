class PlausibleThirdParty {
  constructor() {
    window.plausible =
      window.plausible ||
      function () {
        (window.plausible.q = window.plausible.q || []).push(arguments);
      };
  }

  track(event, data) {
    window.plausible(event, { props: data });
  }
}

export default PlausibleThirdParty;
