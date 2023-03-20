import { FaFacebook, FaTwitter } from 'react-icons/fa';

const SOCIAL_TYPES = {
  twitter: {
    icon: <FaTwitter size={13} />,
    url: 'https://twitter.com/intent/tweet?url=https://app.electricitymaps.com',
    classes: 'bg-[#1d9bf0] hover:bg-[#0c7abf]',
    text: 'Tweet',
  },
  facebook: {
    icon: <FaFacebook size={13} />,
    url: 'https://facebook.com/sharer/sharer.php?u=https%3A%2F%2Fapp.electricitymaps.com%2F',
    classes: 'bg-[#3b5998] hover:bg-[#2d4373]',
    text: 'Share',
  },
  slack: {
    icon: (
      <svg
        className="h-[12px] w-[12px]"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 122.8 122.8"
      >
        <path
          d="M25.8 77.6c0 7.1-5.8 12.9-12.9 12.9S0 84.7 0 77.6s5.8-12.9 12.9-12.9h12.9v12.9zm6.5 0c0-7.1 5.8-12.9 12.9-12.9s12.9 5.8 12.9 12.9v32.3c0 7.1-5.8 12.9-12.9 12.9s-12.9-5.8-12.9-12.9V77.6z"
          fill="#e01e5a"
        ></path>
        <path
          d="M45.2 25.8c-7.1 0-12.9-5.8-12.9-12.9S38.1 0 45.2 0s12.9 5.8 12.9 12.9v12.9H45.2zm0 6.5c7.1 0 12.9 5.8 12.9 12.9s-5.8 12.9-12.9 12.9H12.9C5.8 58.1 0 52.3 0 45.2s5.8-12.9 12.9-12.9h32.3z"
          fill="#36c5f0"
        ></path>
        <path
          d="M97 45.2c0-7.1 5.8-12.9 12.9-12.9s12.9 5.8 12.9 12.9-5.8 12.9-12.9 12.9H97V45.2zm-6.5 0c0 7.1-5.8 12.9-12.9 12.9s-12.9-5.8-12.9-12.9V12.9C64.7 5.8 70.5 0 77.6 0s12.9 5.8 12.9 12.9v32.3z"
          fill="#2eb67d"
        ></path>
        <path
          d="M77.6 97c7.1 0 12.9 5.8 12.9 12.9s-5.8 12.9-12.9 12.9-12.9-5.8-12.9-12.9V97h12.9zm0-6.5c-7.1 0-12.9-5.8-12.9-12.9s5.8-12.9 12.9-12.9h32.3c7.1 0 12.9 5.8 12.9 12.9s-5.8 12.9-12.9 12.9H77.6z"
          fill="#ecb22e"
        ></path>
      </svg>
    ),
    url: 'https://slack.electricitymaps.com',
    classes: 'hover:bg-[#762277] bg-[#4A154B]',
    text: 'Join Slack',
  },
};

export function SocialButton({ type }: { type: keyof typeof SOCIAL_TYPES }) {
  return (
    <a
      href={SOCIAL_TYPES[type].url}
      target="_blank"
      rel="noopener noreferrer"
      className={`${SOCIAL_TYPES[type].classes}  flex items-center space-x-1 rounded  p-0.5 px-2 text-sm font-bold text-white transition-colors`}
    >
      {SOCIAL_TYPES[type].icon}
      <span>{SOCIAL_TYPES[type].text}</span>
    </a>
  );
}

export default function SocialButtons() {
  return (
    <div className="flex space-x-1">
      <SocialButton type="facebook" />
      <SocialButton type="twitter" />
      <SocialButton type="slack" />
    </div>
  );
}
