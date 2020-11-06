import { supportsGoWithoutReloadUsingHash } from "history/DOMUtils";
import React, { useEffect, useState } from "react";
import { default as zonesInfo } from "../../../../../config/zones.json";
// TODO: Remove all unecessary id and class tags
const action_hasdata = resolvePath("images/contrib-actions/action_hasdata.png");
const action_contact = resolvePath("images/contrib-actions/action_contact.png");
const action_hasnothing = resolvePath(
  "images/contrib-actions/action_hasnothing.png"
);

const HasNothing = () => (
  <div>
    <img className="contribute" src={action_hasnothing} alt={"No data"} />
    <h2>No data is currently available for this region</h2>
    <p>electricityMap is powered by our open-source community</p>
    <p>
      Currently no data source has been identified that could allow us to put
      this region on the map.
    </p>
    <h2>What can you do?</h2>
    <h3>1) Add contact details of organisations that may have this data</h3>
    <p>
      Organisations in this region most likely have data that is not shared
      openly yet. Help us find the relevant email and social media information
      so the electricityMap community can reach out and ask for this data by
      adding contact details here:
    </p>
    <h3>Add a data source</h3>
    <p>
      If you know where we can find real-time data about electricity in this
      country, you can help us add data on the map by sharing the data source on
      Github here: If you know how to code, you can even code the parser
      yourself by following this guide:
      <br />
      <a href="https://github.com/tmrowco/electricitymap-contrib/wiki" target="_blank">Github Wiki </a>
    </p>
  </div>
);

const HasData = ({githubIssues}) => (
  <div>
    <img className="contribute" src={action_hasdata} alt={"Parser"} />
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
    <GithubIssues 
    githubIssues={githubIssues}
    />
  </div>
);

const HasContacts = ({ contacts }) => (
  <div>
    <img className="contribute" src={action_contact} alt={"Contact"} />
    <h2>No data is currently available for this region</h2>
    <p>electricityMap is powered by our open-source community</p>
    <p>
      Currently no data source has been identified that could allow us to put
      this region on the map.
    </p>

    <h2>What can you do?</h2>

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
    <h3>Add a data source</h3>
    <p>
      If you know where we can find real-time data about electricity in this
      country, you can help us add data on the map by sharing the data source on
      Github here:
    </p>
    <a href="https://github.com/tmrowco/electricitymap-contrib/issues" target="_blank">Github </a>
  </div>
);

const GithubIssues = ({githubIssues}) => {
    if (!githubIssues || githubIssues.length < 1) {
      return null;
    }

    return (
      <React.Fragment>
        <h2>Github issues</h2>
        <ul>
          {(githubIssues || []).map((issue) => {
            return (
              <li key={issue.title}>
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

function renderContacts(contacts) {
  if (!contacts) return null;
  return (
    <React.Fragment>
      <h3>Contact organisations that may have this data</h3>
      <p>
        These organisations have been mentioned by the community as potential
        sources for data. Reach out to them and ask them to share that data!
      </p>
      {contacts.map((contact) => (
        <div className="contact-item" key={contact.name}>
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

const NoParserInfo = ({ zoneId }) => {
  const [githubIssues, setGithubIssues] = React.useState(null);
  const [githubLabels, setGithubLabels] = React.useState(null);

  // Predicates
  const [hasContacts, setHasContacts] = React.useState(false);
  const [parserBuildable, setParserBuildable] = React.useState(false);

  function zonesContainsKey(key) {
    if (zonesInfo[zoneId]) {
        console.log(zonesInfo[zoneId][key]);
      if (zonesInfo[zoneId][key]) return true;
    }
    return false;
  }

  useEffect(() => {
    setHasContacts(zonesContainsKey("data_contacts"));
    fetchGithubStatus();
  }, [zoneId]);

  function fetchGithubStatus() {
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
          setGithubLabels([]);
          setParserBuildable(false);
        } else {
          // currently there can only be one issue containing the zoneid
          const issues = [{ title: result[0].title, url: result[0].html_url }];
          const labels = result[0].labels;
          setGithubLabels(labels);
          setGithubIssues(issues);
          setParserBuildable(
            labels.some((e) => e.name === "parser buildable!")
          );
        }
      })
      .catch((error) => console.log("error", error));
  }

  if (parserBuildable) {
    return <HasData githubIssues={githubIssues}/>;
  }

  if (zonesContainsKey("data_contacts")) {
    return <HasContacts contacts={zonesInfo[zoneId].data_contacts} />;
  }

  return <HasNothing></HasNothing>;
};

export default NoParserInfo;
