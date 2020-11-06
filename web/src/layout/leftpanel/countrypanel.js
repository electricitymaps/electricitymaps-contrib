/* eslint-disable jsx-a11y/anchor-has-content */
/* eslint-disable jsx-a11y/mouse-events-have-key-events */
/* eslint-disable react/jsx-no-target-blank */
// TODO: re-enable rules

import React, { useEffect, useState } from "react";
import {
  Redirect,
  Link,
  useLocation,
  useParams,
  useHistory,
} from "react-router-dom";
import { connect, useSelector } from "react-redux";
import { noop } from "lodash";
import moment from "moment";

// Components
import LowCarbonInfoTooltip from "../../components/tooltips/lowcarboninfotooltip";
import CircularGauge from "../../components/circulargauge";
import ContributorList from "../../components/contributorlist";
import CountryHistoryCarbonGraph from "../../components/countryhistorycarbongraph";
import CountryHistoryEmissionsGraph from "../../components/countryhistoryemissionsgraph";
import CountryHistoryMixGraph from "../../components/countryhistorymixgraph";
import CountryHistoryPricesGraph from "../../components/countryhistorypricesgraph";
import CountryTable from "../../components/countrytable";
import LoadingPlaceholder from "../../components/loadingplaceholder";

import { dispatchApplication } from "../../store";

// Modules
import { useCurrentZoneData } from "../../hooks/redux";
import { useCo2ColorScale } from "../../hooks/theme";
import { useTrackEvent } from "../../hooks/tracking";
import { flagUri } from "../../helpers/flags";
import { getFullZoneName, __ } from "../../helpers/translation";
import { default as zonesInfo } from "../../../../config/zones.json";

// TODO: Move all styles from styles.css to here
// TODO: Remove all unecessary id and class tags

const action_hasdata = resolvePath("images/contrib-actions/action_hasdata.png");
const action_contact = resolvePath("images/contrib-actions/action_contact.png");
const action_hasnothing = resolvePath(
  "images/contrib-actions/action_hasnothing.png"
);

const CountryLowCarbonGauge = (props) => {
  const electricityMixMode = useSelector(
    (state) => state.application.electricityMixMode
  );

  const d = useCurrentZoneData();
  if (!d) {
    return <CircularGauge {...props} />;
  }

  const fossilFuelRatio =
    electricityMixMode === "consumption"
      ? d.fossilFuelRatio
      : d.fossilFuelRatioProduction;
  const countryLowCarbonPercentage =
    fossilFuelRatio !== null ? 100 - fossilFuelRatio * 100 : null;

  return <CircularGauge percentage={countryLowCarbonPercentage} {...props} />;
};

const CountryRenewableGauge = (props) => {
  const electricityMixMode = useSelector(
    (state) => state.application.electricityMixMode
  );

  const d = useCurrentZoneData();
  if (!d) {
    return <CircularGauge {...props} />;
  }

  const renewableRatio =
    electricityMixMode === "consumption"
      ? d.renewableRatio
      : d.renewableRatioProduction;
  const countryRenewablePercentage =
    renewableRatio !== null ? renewableRatio * 100 : null;

  return <CircularGauge percentage={countryRenewablePercentage} {...props} />;
};

const mapStateToProps = (state) => ({
  electricityMixMode: state.application.electricityMixMode,
  isMobile: state.application.isMobile,
  tableDisplayEmissions: state.application.tableDisplayEmissions,
  zones: state.data.grid.zones,
});

const CountryPanel = ({
  electricityMixMode,
  isMobile,
  tableDisplayEmissions,
  zones,
}) => {
  const [tooltip, setTooltip] = useState(null);
  const [dataState, setDataState] = useState(null);
  const [githubIssues, setGithubIssues] = useState(null);

  const isLoadingHistories = useSelector(
    (state) => state.data.isLoadingHistories
  );
  const co2ColorScale = useCo2ColorScale();

  const trackEvent = useTrackEvent();
  const history = useHistory();
  const location = useLocation();
  const { zoneId } = useParams();

  const data = useCurrentZoneData() || {};

  const parentPage = {
    pathname: isMobile ? "/ranking" : "/map",
    search: location.search,
  };

  // Back button keyboard navigation
  useEffect(() => {
    const keyHandler = (e) => {
      if (e.key === "Backspace" || e.key === "/") {
        history.push(parentPage);
      }
    };
    document.addEventListener("keyup", keyHandler);
    return () => {
      document.removeEventListener("keyup", keyHandler);
    };
  }, [history]);

  useEffect(() => {
    setDataState(null);
    if (zonesInfo[zoneId] && zonesInfo[zoneId].data_contacts) {
      if (zonesInfo[zoneId].data_contacts.length > 0) {
        setDataState("contact");
      }
      return;
    }

    let requestOptions = {
      method: "GET",
      redirect: "follow",
    };

    fetch(
      `https://api.github.com/repos/tmrowco/electricitymap-contrib/issues?labels=zone%3A${zoneId}`,
      requestOptions
    )
      .then((response) => response.json())
      .then((result) => {
        if (result.length < 1) {
          setGithubIssues([]);
          setDataState(null);
        } else {
          console.log(result);
          setDataState(result[0].labels[0].name);
          const issues = [{ title: result[0].title, url: result[0].html_url }];
          setGithubIssues(issues);
          console.log(issues);
        }
      })
      .catch((error) => console.log("error", error));
  }, [zoneId]);

  // Redirect to the parent page if the zone is invalid.
  if (!zones[zoneId]) {
    return <Redirect to={parentPage} />;
  }

  const { hasParser } = data;
  const datetime = data.stateDatetime || data.datetime;
  const co2Intensity =
    electricityMixMode === "consumption"
      ? data.co2intensity
      : data.co2intensityProduction;

  const renderNoParserInfo = () => {
    const hasContacts = zonesInfo[zoneId] && zonesInfo[zoneId].data_contacts;
    switch (dataState) {
      case "parser buildable!":
        return <HasData />;
      case "contact":
        if (hasContacts) {
          return (
            <HasContacts
              contacts={
                zonesInfo[zoneId] ? zonesInfo[zoneId].data_contacts : null
              }
            />
          );
        }
      case "delayed":
        return (
          <HasDelay
            delay={zonesInfo[zoneId].delay}
            contacts={
              zonesInfo[zoneId] ? zonesInfo[zoneId].data_contacts : null
            }
          />
        );
      default:
        return <HasNothing />;
    }
  };

  const switchToZoneEmissions = () => {
    dispatchApplication("tableDisplayEmissions", true);
    trackEvent("switchToCountryEmissions");
  };

  const switchToZoneProduction = () => {
    dispatchApplication("tableDisplayEmissions", false);
    trackEvent("switchToCountryProduction");
  };

  const GithubIssues = () => {
    if (!githubIssues || githubIssues.length < 1) {
      return null;
    }

    return (
      <React.Fragment>
        <h2>Github issues</h2>
        <ul>
          {(githubIssues || []).map((issue) => {
            return (
              <li>
                <a key={issue.title} target="_blank" href={issue.url}>
                  {issue.title}
                </a>
              </li>
            );
          })}
        </ul>
      </React.Fragment>
    );
  };

  return (
    <div className="country-panel">
      <div id="country-table-header">
        <div className="left-panel-zone-details-toolbar">
          <Link to={parentPage}>
            <span className="left-panel-back-button">
              <i className="material-icons" aria-hidden="true">
                arrow_back
              </i>
            </span>
          </Link>
          <div className="country-name-time">
            <div className="country-name-time-table">
              <div style={{ display: "table-cell" }}>
                <img
                  id="country-flag"
                  className="flag"
                  alt=""
                  src={flagUri(zoneId, 24)}
                />
              </div>

              <div style={{ display: "table-cell" }}>
                <div className="country-name">{getFullZoneName(zoneId)}</div>
                <div className="country-time">
                  {datetime ? moment(datetime).format("LL LT") : ""}
                </div>
              </div>
            </div>
          </div>
        </div>

        {hasParser && (
          <React.Fragment>
            <div className="country-table-header-inner">
              <div className="country-col country-emission-intensity-wrap">
                <div
                  id="country-emission-rect"
                  className="country-col-box emission-rect emission-rect-overview"
                  style={{ backgroundColor: co2ColorScale(co2Intensity) }}
                >
                  <div>
                    <span className="country-emission-intensity">
                      {Math.round(co2Intensity) || "?"}
                    </span>
                    g
                  </div>
                </div>
                <div className="country-col-headline">
                  {__("country-panel.carbonintensity")}
                </div>
                <div className="country-col-subtext">(gCO₂eq/kWh)</div>
              </div>
              <div className="country-col country-lowcarbon-wrap">
                <div
                  id="country-lowcarbon-gauge"
                  className="country-gauge-wrap"
                >
                  <CountryLowCarbonGauge
                    onClick={
                      isMobile
                        ? (x, y) => setTooltip({ position: { x, y } })
                        : noop
                    }
                    onMouseMove={
                      !isMobile
                        ? (x, y) => setTooltip({ position: { x, y } })
                        : noop
                    }
                    onMouseOut={() => setTooltip(null)}
                  />
                  {tooltip && (
                    <LowCarbonInfoTooltip
                      position={tooltip.position}
                      onClose={() => setTooltip(null)}
                    />
                  )}
                </div>
                <div className="country-col-headline">
                  {__("country-panel.lowcarbon")}
                </div>
                <div className="country-col-subtext" />
              </div>
              <div className="country-col country-renewable-wrap">
                <div
                  id="country-renewable-gauge"
                  className="country-gauge-wrap"
                >
                  <CountryRenewableGauge />
                </div>
                <div className="country-col-headline">
                  {__("country-panel.renewable")}
                </div>
              </div>
            </div>
            <div className="country-show-emissions-wrap">
              <div className="menu">
                <a
                  onClick={switchToZoneProduction}
                  className={!tableDisplayEmissions ? "selected" : null}
                >
                  {__(`country-panel.electricity${electricityMixMode}`)}
                </a>
                |
                <a
                  onClick={switchToZoneEmissions}
                  className={tableDisplayEmissions ? "selected" : null}
                >
                  {__("country-panel.emissions")}
                </a>
              </div>
            </div>
          </React.Fragment>
        )}
      </div>

      <div className="country-panel-wrap">
        {hasParser ? (
          <React.Fragment>
            <div className="bysource">{__("country-panel.bysource")}</div>

            <CountryTable />

            <hr />
            <div className="country-history">
              <span className="country-history-title">
                {__(
                  tableDisplayEmissions
                    ? "country-history.emissions24h"
                    : "country-history.carbonintensity24h"
                )}
              </span>
              <br />
              <small className="small-screen-hidden">
                <i className="material-icons" aria-hidden="true">
                  file_download
                </i>{" "}
                <a
                  href="https://data.electricitymap.org/?utm_source=electricitymap.org&utm_medium=referral&utm_campaign=country_panel"
                  target="_blank"
                >
                  {__("country-history.Getdata")}
                </a>
                <span className="pro">
                  <i className="material-icons" aria-hidden="true">
                    lock
                  </i>{" "}
                  pro
                </span>
              </small>
              {/* TODO: Make the loader part of AreaGraph component with inferred height */}
              {isLoadingHistories ? (
                <LoadingPlaceholder height="9.2em" />
              ) : tableDisplayEmissions ? (
                <CountryHistoryEmissionsGraph />
              ) : (
                <CountryHistoryCarbonGraph />
              )}

              <span className="country-history-title">
                {tableDisplayEmissions
                  ? __(
                      `country-history.emissions${
                        electricityMixMode === "consumption"
                          ? "origin"
                          : "production"
                      }24h`
                    )
                  : __(
                      `country-history.electricity${
                        electricityMixMode === "consumption"
                          ? "origin"
                          : "production"
                      }24h`
                    )}
              </span>
              <br />
              <small className="small-screen-hidden">
                <i className="material-icons" aria-hidden="true">
                  file_download
                </i>{" "}
                <a
                  href="https://data.electricitymap.org/?utm_source=electricitymap.org&utm_medium=referral&utm_campaign=country_panel"
                  target="_blank"
                >
                  {__("country-history.Getdata")}
                </a>
                <span className="pro">
                  <i className="material-icons" aria-hidden="true">
                    lock
                  </i>{" "}
                  pro
                </span>
              </small>
              {/* TODO: Make the loader part of AreaGraph component with inferred height */}
              {isLoadingHistories ? (
                <LoadingPlaceholder height="11.2em" />
              ) : (
                <CountryHistoryMixGraph />
              )}

              <span className="country-history-title">
                {__("country-history.electricityprices24h")}
              </span>
              {/* TODO: Make the loader part of AreaGraph component with inferred height */}
              {isLoadingHistories ? (
                <LoadingPlaceholder height="7.2em" />
              ) : (
                <CountryHistoryPricesGraph />
              )}
            </div>
            <hr />
            <div>
              {__("country-panel.source")}
              {": "}
              <a
                href="https://github.com/tmrowco/electricitymap-contrib/blob/master/DATA_SOURCES.md#real-time-electricity-data-sources"
                target="_blank"
              >
                <span className="country-data-source">
                  {data.source || "?"}
                </span>
              </a>
              <small>
                {" "}
                (
                <span
                  dangerouslySetInnerHTML={{
                    __html: __(
                      "country-panel.addeditsource",
                      "https://github.com/tmrowco/electricitymap-contrib/tree/master/parsers"
                    ),
                  }}
                />
                )
              </small>{" "}
              {__("country-panel.helpfrom")}
              <ContributorList />
            </div>
          </React.Fragment>
        ) : (
          <div className="zone-details-no-parser-message">
            {renderNoParserInfo()}
            {/* <span dangerouslySetInnerHTML={{ __html: __('country-panel.noParserInfo', 'https://github.com/tmrowco/electricitymap-contrib#add-a-new-region') }} /> */}

            {GithubIssues()}
            {/* {(githubIssues || []).map((issue) => <a href={issue.url}>{issue.title}</a>)} */}
          </div>
        )}

        <div className="social-buttons large-screen-hidden">
          <div>
            {/* Facebook share */}
            <div
              className="fb-share-button"
              data-href="https://www.electricitymap.org/"
              data-layout="button_count"
            />
            {/* Twitter share */}
            <a
              className="twitter-share-button"
              data-url="https://www.electricitymap.org"
              data-via="electricitymap"
              data-lang={locale}
            />
            {/* Slack */}
            <span className="slack-button">
              <a
                href="https://slack.tmrow.com"
                target="_blank"
                className="slack-btn"
              >
                <span className="slack-ico" />
                <span className="slack-text">Slack</span>
              </a>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

const HasNothing = () => (
  <div>
    <img className="contribute" src={action_hasnothing} alt={"All pls"} />
    <h2>No data is currently available for this region</h2>
    <p>electricityMap is powered by our open-source community</p>
    <p>
      Currently no data source has been identified that could allow us to put
      this region on the map.
    </p>
    <h2>What can you do?</h2>
    <p>1) Add contact details of organisations that may have this data</p>
    <p>
      Organisations in this region most likely have data that is not shared
      openly yet. Help us find the relevant email and social media information
      so the electricityMap community can reach out and ask for this data by
      adding contact details here:
    </p>
    <p>2) Add a data source</p>
    <p>
      If you know where we can find real-time data about electricity in this
      country, you can help us add data on the map by sharing the data source on
      Github here: If you know how to code, you can even code the parser
      yourself by following this guide:
      <br />
      <a href="#">A great guide </a>
    </p>
  </div>
);

const HasData = () => (
  <div>
    <img className="contribute" src={action_hasdata} alt={"Parser pls"} />
    <h2>Data has been found for this region</h2>
    <p>electricityMap is powered by our open-source community</p>
    <p>
      Good news: a data source has been found and with your help it could be
      added to electricityMap.
    </p>

    <h2>What can you do?</h2>

    <p>
      Follow the current development and contribute on Github to add this data
      to electricityMap.
    </p>
  </div>
);

const HasContacts = ({ contacts }) => (
  <div>
    <img className="contribute" src={action_contact} alt={"Contact pls"} />
    <h2>No data is currently available for this region</h2>
    <p>electricityMap is powered by our open-source community</p>
    <p>
      Currently no data source has been identified that could allow us to put
      this region on the map.
    </p>

    <h2>What can you do?</h2>

    <h3>1) Contact organisations that may have this data</h3>
    <p>
      These organisations have been mentioned by the community as potential
      sources for data. Reach out to them and ask them to share that data!
    </p>
    {contacts.map((contact) => (
      <div className="contact-item">
        <p>
          <strong>{contact.name}</strong>
        </p>
        <p>Email: {contact.email}</p>
        <p>Twitter: {contact.twitter}</p>
      </div>
    ))}
    <h3>2) Add a data source</h3>
    <p>
      If you know where we can find real-time data about electricity in this
      country, you can help us add data on the map by sharing the data source on
      Github here:
    </p>
  </div>
);

function renderContacts(contacts) {
  return (
    <React.Fragment>
      <h3>Contact organisations that may have this data</h3>
      <p>
        These organisations have been mentioned by the community as potential
        sources for data. Reach out to them and ask them to share that data!
      </p>
      {contacts.map((contact) => (
        <div className="contact-item">
          <p>
            <strong>{contact.name}</strong>
          </p>
          <p>Email: {contact.email}</p>
          <p>Twitter: {contact.twitter}</p>
        </div>
      ))}
    </React.Fragment>
  );
}

const HasDelay = ({ delay, contacts }) => (
  <div>
    <img className="contribute" src={action_contact} alt={"Contact pls"} />
    <h2>Data is delayed for this zone</h2>
    <p>electricityMap is powered by our open-source community</p>
    <h2>What can you do?</h2>
    {renderContacts(contacts)}
    <h3>Add a data source</h3>
    <p>
      If you know where we can find real-time data about electricity in this
      country, you can help us add data on the map by sharing the data source on
      Github here:
    </p>
  </div>
);

export default connect(mapStateToProps)(CountryPanel);
