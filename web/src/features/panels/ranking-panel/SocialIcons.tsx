import { FacebookButton } from 'components/buttons/FacebookButton';
import { FeedbackButton } from 'components/buttons/FeedbackButton';
import { LinkedinButton } from 'components/buttons/LinkedinButton';
import { TwitterButton } from 'components/buttons/TwitterButton';
import { useTranslation } from 'react-i18next';

export default function SocialIconRow() {
  const { t } = useTranslation();

  return (
    <div className="flex w-full items-center justify-between gap-1">
      <section className="flex items-center gap-1">
        <h3>{t('info.share-app')}</h3>
        <FacebookButton isIconOnly size="sm" type="link" isShareLink />
        <LinkedinButton isIconOnly size="sm" type="link" isShareLink />
        <TwitterButton isIconOnly size="sm" type="link" isShareLink />
      </section>
      <FeedbackButton size="sm" type="link" />
    </div>
  );
}
