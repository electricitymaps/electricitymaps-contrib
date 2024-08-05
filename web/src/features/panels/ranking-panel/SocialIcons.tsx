import { FacebookButton } from 'components/buttons/FacebookButton';
import { FeedbackButton } from 'components/buttons/FeedbackButton';
import { LinkedinButton } from 'components/buttons/LinkedinButton';
import { TwitterButton } from 'components/buttons/TwitterButton';

export default function SocialIconRow() {
  return (
    <div className="flex w-full items-center gap-1">
      <h3>Share the app:</h3>
      <div className="mr-auto flex space-x-1">
        <FacebookButton isIconOnly size="sm" type="link" isShareLink />
        <LinkedinButton isIconOnly size="sm" type="link" isShareLink />
        <TwitterButton isIconOnly size="sm" type="link" isShareLink />
      </div>
      <FeedbackButton size="sm" type="link" />
    </div>
  );
}
