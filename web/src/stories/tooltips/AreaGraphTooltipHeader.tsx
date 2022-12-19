import { useTranslation } from 'react-i18next';
import { modeColor, TimeAverages } from 'utils/constants';
import { formatDate } from 'utils/formatting';

interface AreaGraphToolTipHeaderProps {
  squareColor: string;
  datetime: Date;
  timeAverage: TimeAverages;
  title: string;
}

export default function AreaGraphToolTipHeader(props: AreaGraphToolTipHeaderProps) {
  const { squareColor, datetime, timeAverage, title } = props;
  const { i18n } = useTranslation();

  return (
    <>
      <div className="mb-2 flex justify-between">
        <div className="inline-flex items-center gap-x-1 font-bold">
          <div
            style={{
              backgroundColor: squareColor,
              height: 16,
              width: 16,
            }}
            className="rounded-sm font-bold"
          ></div>
          <p className="text-base">{title}</p>
        </div>
        <div className="my-1 h-[32px] max-w-[160px] select-none rounded-full bg-brand-green/10 py-2 px-3 text-sm text-brand-green dark:bg-gray-700 dark:text-white">
          {formatDate(datetime, i18n.language, timeAverage)}
        </div>
      </div>
      <hr className="my-1 mb-3" />
    </>
  );
}
