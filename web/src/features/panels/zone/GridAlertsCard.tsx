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
      <div className="flex flex-col items-center gap-2 rounded-lg bg-sunken p-4 dark:bg-sunken-dark">
        <img
          src="/images/empty_chart_illustration.svg"
          alt="Empty chart"
          className="mr-1 inline h-20 w-20 dark:hidden"
        />
        <img
          src="/images/empty_chart_illustration_dark.svg"
          alt="Empty chart"
          className="mr-1 hidden h-20 w-20 dark:block"
        />
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
