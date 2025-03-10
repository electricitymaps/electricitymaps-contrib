import { Button, ButtonProps } from 'components/Button';
import { useTranslation } from 'react-i18next';
import { FaGithub } from 'react-icons/fa6';
import trackEvent from 'utils/analytics';
import { DEFAULT_ICON_SIZE, TrackEvent } from 'utils/constants';

interface GithubButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'onClick' | 'backgroundClasses' | 'foregroundClasses'
  > {
  iconSize?: number;
  isIconOnly?: boolean;
}

export function GithubButton({
  isIconOnly,
  iconSize = DEFAULT_ICON_SIZE,
  ...restProps
}: GithubButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      backgroundClasses="bg-[#010409]"
      foregroundClasses="text-white dark:text-white focus-visible:outline-[#010409]"
      href="https://github.com/electricityMaps/electricitymaps-contrib"
      icon={<FaGithub size={iconSize} />}
      onClick={() => {
        trackEvent(TrackEvent.CONTRIBUTE_ON_GITHUB_BUTTON_CLICKED);
      }}
      {...restProps}
    >
      {isIconOnly ? undefined : t('button.github')}
    </Button>
  );
}
