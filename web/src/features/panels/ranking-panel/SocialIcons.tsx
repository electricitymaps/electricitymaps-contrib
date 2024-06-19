import { FaFacebook, FaLinkedin, FaSlack, FaTwitter } from 'react-icons/fa';

interface SocialType {
  icon: JSX.Element;
  url: string;
  color: string;
  text: string;
}

interface SocialTypes {
  [key: string]: SocialType;
}

const SOCIAL_TYPES: SocialTypes = {
  twitter: {
    icon: <FaTwitter size={16} color="#1d9bf0" />,
    url: 'https://twitter.com/intent/tweet?url=https://app.electricitymaps.com',
    color: '#1d9bf0',
    text: 'Tweet',
  },
  facebook: {
    icon: <FaFacebook size={16} color="#4267B2" />,
    url: 'https://facebook.com/sharer/sharer.php?u=https%3A%2F%2Fapp.electricitymaps.com%2F',
    color: '#4267B2',
    text: 'Share',
  },
  slack: {
    icon: <FaSlack size={16} color="#4A154B" />,
    url: 'https://slack.electricitymaps.com',
    color: '#4A154B',
    text: 'Join Slack',
  },
  linkedin: {
    icon: <FaLinkedin size={16} color="#0077B5" />,
    url: 'https://www.linkedin.com/shareArticle?mini=true&url=https://app.electricitymaps.com',
    color: '#0077B5',
    text: 'Share',
  },
};

export function SocialIcon({ type }: { type: keyof typeof SOCIAL_TYPES }) {
  return (
    <a href={SOCIAL_TYPES[type].url} className="text-white">
      {SOCIAL_TYPES[type].icon}
    </a>
  );
}

export default function SocialIcons() {
  return (
    <div className="flex space-x-1">
      <SocialIcon type="twitter" />
      <SocialIcon type="facebook" />
      <SocialIcon type="linkedin" />
    </div>
  );
}
