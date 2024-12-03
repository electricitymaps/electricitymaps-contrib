import { ONE_HOUR } from 'api/helpers';
import { Toast, useToastReference } from 'components/Toast';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useRegisterSW } from 'virtual:pwa-register/react';

function UpdatePrompt() {
  const reference = useToastReference();
  const { t } = useTranslation();
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegisteredSW: (_swURL, registration) => {
      if (registration) {
        const checkForUpdates = async () => {
          console.info('Checking for app update...');
          try {
            await registration.update();
          } catch (error) {
            console.warn('Failed to check for updates:', error);
          }
        };

        setInterval(checkForUpdates, import.meta.env.PROD ? ONE_HOUR : 10 * 1000);
      }
    },
    onRegisterError(error) {
      console.warn('SW registration failed:', error);
    },
  });

  const close = () => setNeedRefresh(false);

  const update = () => updateServiceWorker(true);

  useEffect(() => {
    if (needRefresh) {
      reference.current?.publish();
    }
  }, [needRefresh, reference]);

  return (
    <Toast
      ref={reference}
      description={t('updatePrompt.description')}
      toastAction={update}
      isCloseable={true}
      toastActionText={t('updatePrompt.update')}
      toastClose={close}
      toastCloseText={t('updatePrompt.dismiss')}
      duration={60 * 1000}
    />
  );
}

export default UpdatePrompt;
