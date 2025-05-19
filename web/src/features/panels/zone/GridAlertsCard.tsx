import { ChartSubtitle, ChartTitle } from 'features/charts/ChartTitle';
import { RoundedCard } from 'features/charts/RoundedCard';
import { FaGithub } from 'react-icons/fa6';
import { RiSurveyFill } from 'react-icons/ri';
import { Charts, DEFAULT_ICON_SIZE, TimeRange } from 'utils/constants';

export default function GridAlertsCard({
  datetimes,
  timeRange,
}: {
  datetimes: Date[];
  timeRange: TimeRange;
  displayByEmissions: boolean;
}) {
  return (
    <RoundedCard>
      <ChartTitle
        titleText="Reported grid alerts"
        id={Charts.ELECTRICITY_GRID_ALERT}
        subtitle={<ChartSubtitle datetimes={datetimes} timeRange={timeRange} />}
        isMoreOptionsHidden={true}
      />
      <div className="flex flex-col items-center gap-2 rounded-lg bg-gray-100 p-4">
        <div className="relative h-[76px] w-[76px] overflow-hidden">
          <div className="absolute left-[43.5px] top-[1px] h-[54px] w-[25px] rounded border border-[#CCC] bg-[#FAFAFA]" />
          <div className="absolute left-[25.5px] top-[21px] h-[44px] w-[25px] rounded border border-[#CCC] bg-[#FAFAFA]" />
          <div className="absolute left-[7.5px] top-[43px] h-[32px] w-[25px] rounded border border-[#CCC] bg-[#FAFAFA]" />
          <div className="absolute left-[8.5px] top-[44.5px] h-[13px] w-[23px] rounded-sm bg-[#EAEAEA]" />
          <div className="absolute left-[44.5px] top-[2.5px] h-[13px] w-[23px] rounded-sm bg-[#EAEAEA]" />
          <div className="absolute left-[26.5px] top-[22.5px] h-[13px] w-[23px] rounded-sm bg-[#EAEAEA]" />
        </div>
        <p className="text-center text-xs">
          We&apos;re missing data. Help us{' '}
          <a
            href="https://github.com/electricitymaps/electricitymaps-contrib/issues/8121"
            target="_blank"
            className="font-semibold text-emerald-800 underline underline-offset-2 dark:text-emerald-500"
            rel="noopener"
          >
            <FaGithub size={DEFAULT_ICON_SIZE} className="inline" /> shape this feature
          </a>{' '}
          or tell us about your{' '}
          <a
            href="https://docs.google.com/forms/d/e/1FAIpQLSdVgjBHiune743TVvPyR1ydE4oY8znbO5jZHNyTbsT_dXCsvg/formResponse"
            target="_blank"
            className="font-semibold text-emerald-800 underline underline-offset-2 dark:text-emerald-500"
            rel="noopener"
          >
            <RiSurveyFill className="inline" /> ideas and experience
          </a>
          .
        </p>
      </div>
    </RoundedCard>
  );
}
