import { Toast, ToastType, useToastReference } from 'components/Toast';
import { useAtom } from 'jotai';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { isRedirectedToLatestDatetimeAtom } from 'utils/state/atoms';

function DateRedirectToast() {
  const reference = useToastReference();
  const { t } = useTranslation();
  const [isRedirectedToLatestDatetime, setIsRedirectedToLatestDatetime] = useAtom(
    isRedirectedToLatestDatetimeAtom
  );
  const TOAST_DURATION = 10 * 1000; // 10s

  useEffect(() => {
    if (isRedirectedToLatestDatetime) {
      reference.current?.publish();
    }
    setIsRedirectedToLatestDatetime(false);
  }, [isRedirectedToLatestDatetime, reference, setIsRedirectedToLatestDatetime]);

  return (
    <Toast
      ref={reference}
      description={t('time-controller.date-unavailable')}
      duration={TOAST_DURATION}
      type={ToastType.INFO}
      className="h-fit"
    />
  );
}

export default DateRedirectToast;
