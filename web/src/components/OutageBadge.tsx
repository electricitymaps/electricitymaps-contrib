import Badge from 'components/Badge';
import { useTranslation } from 'react-i18next';

export default function OutageBadge() {
  const { t } = useTranslation();

  return (
    <Badge
      type={'warning'}
      icon={
        "h-[12px] w-[12px] mt-[1px] bg-[url('/images/warning_light.svg')] bg-center dark:bg-[url('/images/warning_dark.svg')]"
      }
      pillText={t('estimation-badge.outage')}
    />
  );
}
