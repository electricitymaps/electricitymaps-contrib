import Link from 'components/Link';
import { useTranslation } from 'react-i18next';

export default function InfoText() {
  const { t } = useTranslation();
  return (
    <div className="prose dark:prose-invert prose-p:my-1 prose-p:leading-snug prose-a:no-underline hover:prose-a:underline">
      <p className="mb-4">
        <Link href="https://electricitymaps.com/?utm_source=app.electricitymaps.com&utm_medium=referral&utm_campaign=about-section">
          Electricity Maps
        </Link>{' '}
        {t('info.text')}
      </p>
    </div>
  );
}
