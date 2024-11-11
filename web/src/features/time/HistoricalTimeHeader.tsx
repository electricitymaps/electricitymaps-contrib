import useGetState from 'api/getState';
import Badge from 'components/Badge';
import { Button } from 'components/Button';
import { FormattedTime } from 'components/Time';
import { useAtomValue } from 'jotai';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';
import { useNavigateWithParameters } from 'utils/helpers';
import { endDatetimeAtom, startDatetimeAtom } from 'utils/state/atoms';

export default function TimeHeader() {
  const { i18n } = useTranslation();
  const startDatetime = useAtomValue(startDatetimeAtom);
  const endDatetime = useAtomValue(endDatetimeAtom);
  const { isLoading } = useGetState();
  const { urlDatetime } = useParams();
  const navigate = useNavigateWithParameters();
  function handleLeftClick() {
    if (!urlDatetime) {
      return;
    }
    const date = new Date(urlDatetime);
    date.setUTCHours(date.getUTCHours() - 24);
    const newDateString = date.toISOString().slice(0, -5) + 'Z';
    navigate({ datetime: newDateString });
  }
  function handleRightClick() {
    if (!endDatetime) {
      return;
    }

    const date = new Date(endDatetime);
    date.setUTCHours(date.getUTCHours() + 24);
    const now = new Date();
    const twentyFourHoursAgo = new Date(now);
    twentyFourHoursAgo.setUTCHours(now.getUTCHours() - 24);

    if (date >= twentyFourHoursAgo) {
      navigate({ datetime: '' });
      return;
    }

    const newDateString = date.toISOString().slice(0, -5) + 'Z';
    navigate({ datetime: newDateString });
  }
  return (
    <div className="flex min-h-6 flex-row items-center justify-between">
      {!isLoading && startDatetime && endDatetime && (
        <Badge
          pillText={
            <FormattedTime
              datetime={startDatetime}
              language={i18n.languages[0]}
              endDatetime={endDatetime}
            />
          }
          type="success"
        />
      )}
      <div className="flex flex-row items-center gap-2">
        <ChevronLeft onClick={handleLeftClick} className="text-brand-green" />
        <ChevronRight
          onClick={handleRightClick}
          className={twMerge('text-brand-green', !urlDatetime && 'opacity-50')}
        />
        <Button
          size="sm"
          type="secondary"
          onClick={() => {
            navigate({ datetime: '' });
          }}
          isDisabled={!urlDatetime}
        >
          Latest
        </Button>
      </div>
    </div>
  );
}
