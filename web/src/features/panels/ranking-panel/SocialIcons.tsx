import {
  FacebookButton,
  FeedbackButton,
  LinkedinButton,
  TwitterButton,
} from 'components/Button';

export default function SocialIconRow() {
  return (
    <div className="flex w-full">
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
