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
        <TwitterButton iconOnly size="sm" type="link" isShareLink />
        <FacebookButton iconOnly size="sm" type="link" isShareLink />
        <LinkedinButton iconOnly size="sm" type="link" isShareLink />
      </div>
      <FeedbackButton size="sm" type="link" />
    </div>
  );
}
