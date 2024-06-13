import { ONE_HOUR } from 'api/helpers';
import Toast from 'components/Toast';
import { useTranslation } from 'react-i18next';
import { useRegisterSW } from 'virtual:pwa-register/react';

function UpdatePrompt() {
  const { t } = useTranslation();
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegisteredSW: (_swURL, registration) => {
      registration &&
        setInterval(
          () => {
            console.info(`Checking for app update...`);
            registration.update();
          },
          import.meta.env.PROD ? ONE_HOUR : 10 * 1000
        );
    },
    onRegisterError(error) {
      console.error(`SW registration failed: ${error}`);
    },
  });

  const close = () => setNeedRefresh(false);

  const update = () => updateServiceWorker(true);

  return (
    needRefresh && (
      <Toast
        title={t('misc.newversion')}
        toastAction={update}
        isCloseable={true}
        toastActionText={t('misc.reload')}
        toastClose={close}
        duration={60 * 1000}
      />
    )
  );
}

export default UpdatePrompt;
