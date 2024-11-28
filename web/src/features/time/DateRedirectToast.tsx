import { Toast, ToastType, useToastReference } from 'components/Toast';
import { useAtom } from 'jotai';
import { useEffect } from 'react';
import { isRedirectedToLastDatetimeAtom } from 'utils/state/atoms';

function DateRedirectToast() {
  const reference = useToastReference();
  const [isRedirectedToLastDatetime, setIsRedirectedToLastDatetime] = useAtom(
    isRedirectedToLastDatetimeAtom
  );
  const TOAST_DURATION = 100 * 1000; // 10s

  useEffect(() => {
    if (isRedirectedToLastDatetime) {
      reference.current?.publish();
    }
    setIsRedirectedToLastDatetime(false);
  }, [isRedirectedToLastDatetime, reference, setIsRedirectedToLastDatetime]);

  return (
    <Toast
      ref={reference}
      description="This link is beyond the available dates. We've redirected you to the last available date."
      duration={TOAST_DURATION}
      type={ToastType.INFO}
      className="h-fit"
    />
  );
}

export default DateRedirectToast;
