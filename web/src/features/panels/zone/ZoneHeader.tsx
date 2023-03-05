import CarbonIntensitySquare from 'components/CarbonIntensitySquare';
import { CircularGauge } from 'components/CircularGauge';
import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { Mode } from 'utils/constants';
import { productionConsumptionAtom } from 'utils/state/atoms';
import ZoneHeaderTitle from './ZoneHeaderTitle';

function LowCarbonTooltip() {
  const { __ } = useTranslation();
  return (
    <div className="text-left">
      <b>{__('tooltips.lowcarbon')}</b>
      <br />
      <small>{__('tooltips.lowCarbDescription')}</small>
      <br />
    </div>
  );
}

interface ZoneHeaderProps {
  zoneId: string;
  isEstimated?: boolean;
  isAggregated?: boolean;
  co2intensity?: number;
  renewableRatio?: number;
  fossilFuelRatio?: number;
  co2intensityProduction?: number;
  renewableRatioProduction?: number;
  fossilFuelRatioProduction?: number;
}

import React, { useState, useEffect } from "react";

export function ZoneHeader({
  zoneId,
  isEstimated,
  isAggregated,
  co2intensity,
  renewableRatio,
  fossilFuelRatio,
  co2intensityProduction,
  renewableRatioProduction,
  fossilFuelRatioProduction,
}: ZoneHeaderProps) {
  const { __ } = useTranslation();
  const [currentMode] = useAtom(productionConsumptionAtom);
  const isConsumption = currentMode === Mode.CONSUMPTION;
  const intensity = isConsumption ? co2intensity : co2intensityProduction;
  const renewable = isConsumption ? renewableRatio : renewableRatioProduction;
  const fossilFuel =
    (isConsumption ? fossilFuelRatio : fossilFuelRatioProduction) ?? null;

  const [outageData, setOutageData] = useState(null);
  const fetchData = async () => {
    const id = '1C7zULJugzjFj3zw98WZYzBhEIHNYzTtTLFdTcVdzqzc';
    const gid = '0';
    const url = 'https://docs.google.com/spreadsheets/d/'+id+'/gviz/tq?tqx=out:json&tq&gid='+gid;
    const responseText = await (
      await fetch(url)
    ).text();
    const table = JSON.parse(responseText.match(/(?<=.*\().*(?=\);)/s)[0]).table;
    const matching = table.rows.find(d => d.c[0].v === zoneId);
    if (matching) {
      setOutageData({
        'zoneId': matching.c[0].v,
        'message': matching.c[1].v,
        'issueId': matching.c[2].v,
      });
    } else {
      setOutageData(null);
    }
  };
  useEffect(() => {
    fetchData();
  }, [zoneId]);

  return (
    <div className="mt-1 grid w-full gap-y-5 sm:pr-4">
      <ZoneHeaderTitle
        zoneId={zoneId}
        isEstimated={isEstimated}
        isAggregated={isAggregated}
      />

      {outageData && <div
        class="p-2 text-sm"
        style={{
          display: 'inline-flex',
          backgroundColor: '#ffeb3b2b',
          border: '1px #ffc107 solid',
          borderRadius: '7px',
        }}
      >
        <span>
          ⚠️ {outageData.message || 'Data for this zone might contain some inaccuracies'} - read more&nbsp;
          <a href={`https://github.com/electricitymaps/electricitymaps-contrib/issues/${outageData.issueId}`} style={{ color: 'blue' }}>
            <svg style={{ display: 'inline' }} xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
            &nbsp;on this issue (#{outageData.issueId})
          </a>.
        </span>
      </div>}

      <div className="flex flex-row justify-evenly">
        <CarbonIntensitySquare intensity={intensity ?? Number.NaN} withSubtext />
        <CircularGauge
          name={__('country-panel.lowcarbon')}
          ratio={fossilFuel ? 1 - fossilFuel : Number.NaN}
          tooltipContent={<LowCarbonTooltip />}
          testId="zone-header-lowcarbon-gauge"
        />
        <CircularGauge
          name={__('country-panel.renewable')}
          ratio={renewable ?? Number.NaN}
          testId="zone-header-renewable-gauge"
        />
      </div>
    </div>
  );
}
