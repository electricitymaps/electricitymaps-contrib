import Toast from 'components/Toast';
import { useTranslation } from 'react-i18next';
import { useRegisterSW } from 'virtual:pwa-register/react';

function UpdatePrompt() {
  const { t } = useTranslation();
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegisteredSW: (registration) => {
      console.log(`SW registered: ${registration} at ${new Date().toISOString()}`);
    },
    onRegisterError(error) {
      console.error(`SW registration failed: ${error} at ${new Date().toISOString()}`);
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
      />
    )
  );
}

export default UpdatePrompt;
