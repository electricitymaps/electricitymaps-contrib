import React, {FC} from 'react';
import Accordion from 'react-bootstrap/Accordion';
import { Button } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import zonesConfigJSON from './config/zones.json';
import './App.css';
import 'bootstrap/dist/css/bootstrap.min.css';

type outage = {
  github: string;
  description: string;
  status: string;
  estimation_available: boolean;
  workaround_available: boolean;
  known_limitations: string;
}

type zoneConfigItem = {
  contributors?: string[];
  capacity?: any;
  disclaimer?: string;
  timezone?: string | null;
  bounding_box?: any;
  parsers?: any;
  flag_file_name?: string;
  estimation_method?: string;
  outage?: outage;
};

type zoneOutage = {
  zoneKey: string;
  outage?: outage;
}

interface ZonesProps {
  zones: zoneOutage[];
  type: string;
}

const zonesConfig: Record<string, zoneConfigItem | undefined> = zonesConfigJSON;
const zones: zoneOutage[] = Object.entries(zonesConfig).map(([k, v]) => ({
  zoneKey: k,
  outage: v?.outage
}));
const zonesDown = zones.filter(config => config.outage != null && ! (config.outage?.estimation_available || config.outage?.workaround_available));
const zonesWarning = zones.filter(config => config.outage != null && (config.outage?.estimation_available || config.outage?.workaround_available));
const zonesOk = zones.filter(config => !config.outage);
const ZonePanel: FC<ZonesProps> = ({zones, type}) => {
  return (
    <Accordion>
      {zones.map(zone => {return (
        <Accordion.Item eventKey={zone.zoneKey} key={zone.zoneKey} >

        <Accordion.Header className='.bg-warning'>{zone.zoneKey}</Accordion.Header>
        <Accordion.Body>
        {type != "ok" ? <><Button variant="outline-secondary"><a href={zone.outage?.github}>See discussion on Github</a></Button>
        <h3>Description</h3>
        {zone.outage?.description}
        <h3>Status</h3>
        {zone.outage?.status}
        {type === "warning" && <><h3>Limitations of the workaround or estimations</h3>
        {zone.outage?.known_limitations}</>}</> : <>
        <Form>
          <h3>Noticed something weird ? You can submit an issue through this form.</h3>
      <Form.Group className="mb-3" controlId="formBasicEmail">
        <Form.Label>Email address</Form.Label>
        <Form.Control type="email" placeholder="Enter email" />
      </Form.Group>
      <Form.Group className="mb-3" controlId="formBasicEmail">
        <Form.Label>Describe the issue</Form.Label>
        <Form.Control type="input" placeholder="The data has been produced by Mickey Mouse." />
      </Form.Group>
      <Form.Text className="text-muted">
          We will have a look at your report shorthly. If it is confirmed, a Github issue will be created and this page will be updated.
        </Form.Text>
      <Button variant="success">
        Submit
      </Button>
    </Form>
        </>}

        </Accordion.Body>
      </Accordion.Item>
      )})}
    </Accordion>
  )
}
console.log(zonesOk);
function App() {
  return (
    <div className="App">
      <h1 className="text-3xl font-bold">Zone transparency</h1>

      <h2>Zones that are down.</h2>
      <br/>
      {ZonePanel({zones: zonesDown, type: "down"})}
      <h2>Zones with a workaround or estimations.</h2>
      <br/>
      {ZonePanel({zones: zonesWarning, type: "warning"})}
      <h2>No known problems.</h2>
      <br/>
      {ZonePanel({zones: zonesOk, type: "ok"})}
    </div>
  );
}

export default App;
