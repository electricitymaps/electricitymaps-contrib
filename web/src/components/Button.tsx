import { isFAQModalOpenAtom } from 'features/modals/modalAtoms';
import { useSetAtom } from 'jotai/react';
import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  FaCircleInfo,
  FaCommentDots,
  FaFacebook,
  FaGithub,
  FaLinkedin,
  FaSlack,
  FaXTwitter,
} from 'react-icons/fa6';
import { twMerge } from 'tailwind-merge';
import trackEvent from 'utils/analytics';

const DEFAULT_ICON_SIZE = 16;

type SizeOptions = 'sm' | 'md' | 'lg' | 'xl';

interface ButtonProps {
  icon?: React.ReactNode;
  children?: React.ReactNode;
  isDisabled?: boolean;
  size?: SizeOptions;
  shouldShrink?: boolean;
  type?: 'primary' | 'secondary' | 'tertiary' | 'link';
  href?: string;
  backgroundClasses?: string;
  foregroundClasses?: string;
  asDiv?: boolean;
  onClick?: () => void;
}

interface SocialButtonProps
  extends Omit<ButtonProps, 'icon' | 'children' | 'href' | 'onClick'> {
  iconSize?: number;
  isIconOnly?: boolean;
  isShareLink?: boolean;
}

export function Button({
  icon,
  children,
  isDisabled,
  href,
  backgroundClasses, // backgroundColor, borderColor, margin, etc.
  foregroundClasses, // textColor, etc.
  size = 'lg',
  shouldShrink = false,
  type = 'primary',
  asDiv, // If true, renders a div instead of a button to avoid nested buttons in components like ToastPrimitive.Action
  onClick,
}: ButtonProps) {
  const renderAsLink = Boolean(href);
  const As = getComponentType(renderAsLink, asDiv);
  const componentType = renderAsLink ? undefined : 'button';
  const isIconOnly = !children && Boolean(icon);

  return (
    <div
      className={twMerge(
        `items-center justify-center rounded-full ${getBackground(type, isDisabled)}`,
        backgroundClasses,
        shouldShrink ? 'w-fit' : ''
      )}
    >
      <As
        className={twMerge(
          `flex h-full w-full flex-row items-center justify-center rounded-full text-sm font-semibold
        focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-green disabled:text-neutral-400
        disabled:hover:bg-inherit disabled:dark:text-gray-500 ${getSize(
          size,
          type,
          isIconOnly
        )}
        ${getForeground(type)} ${getHover(type)}`,
          foregroundClasses
        )}
        disabled={isDisabled}
        href={href}
        type={componentType}
        onClick={onClick}
        target="_blank"
        // Used to prevent browser translation crashes on edge, see #6809
        translate="no"
      >
        {icon}
        {children}
      </As>
    </div>
  );
}

function getComponentType(renderAsLink: boolean, asDiv?: boolean) {
  if (renderAsLink) {
    return 'a';
  }
  if (asDiv) {
    return 'div';
  }

  return 'button';
}

function getHover(type: string) {
  switch (type) {
    case 'primary': {
      return 'hover:bg-black/20';
    }
    default: {
      return 'hover:bg-neutral-400/10';
    }
  }
}

function getBackground(type: string, disabled: boolean | undefined) {
  switch (type) {
    case 'primary': {
      if (disabled) {
        return 'bg-zinc-50 dark:bg-gray-800 border border-neutral-200 dark:border-gray-700';
      }
      return 'bg-brand-green';
    }
    case 'secondary': {
      return 'border dark:border-gray-700 border-neutral-200 bg-white dark:bg-gray-900';
    }
    default: {
      return 'bg-inherit';
    }
  }
}

function getForeground(type: string) {
  switch (type) {
    case 'primary': {
      return 'text-white';
    }
    case 'link': {
      return 'text-emerald-800 dark:text-emerald-500';
    }
    default: {
      return 'text-black dark:text-white';
    }
  }
}

function getSize(size: SizeOptions, type: string, isIconOnly: boolean) {
  if (isIconOnly) {
    switch (size) {
      case 'sm': {
        return 'min-w-7 min-h-7';
      }
      case 'md': {
        return 'min-w-9 min-h-9';
      }
      case 'lg': {
        return 'min-w-11 min-h-11';
      }
      case 'xl': {
        return 'min-w-14 min-h-14';
      }
    }
  }

  switch (size) {
    case 'sm': {
      return 'min-w-6 min-h-6 px-2 py-1 gap-x-1 text-sm';
    }
    case 'md': {
      return 'min-w-8 min-h-8 px-4 py-2 gap-x-1.5 text-sm';
    }
    case 'lg': {
      return type == 'link'
        ? 'px-4 py-2 gap-x-2 text-sm'
        : 'min-w-10 min-h-10 px-6 py-3 gap-x-1.5 text-sm';
    }
    case 'xl': {
      return type == 'link'
        ? 'px-4 py-2 gap-x-2 text-base'
        : 'min-w-12 min-h-12 px-8 py-4 gap-x-1.5 text-base';
    }
    default: {
      return '';
    }
  }
}

export function FAQButton({
  isIconOnly,
  size = 'lg',
  iconSize = DEFAULT_ICON_SIZE,
  shouldShrink,
}: SocialButtonProps) {
  const { t } = useTranslation();
  const setIsFAQModalOpen = useSetAtom(isFAQModalOpenAtom);
  return (
    <Button
      size={size}
      type="secondary"
      shouldShrink={shouldShrink}
      icon={<FaCircleInfo size={iconSize} />}
      onClick={() => setIsFAQModalOpen(true)}
    >
      {isIconOnly ? undefined : t('button.faq')}
    </Button>
  );
}

export function PrivacyPolicyButton({
  isIconOnly,
  size = 'lg',
  shouldShrink,
}: SocialButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      size={size}
      type="link"
      shouldShrink={shouldShrink}
      href="https://www.electricitymaps.com/privacy-policy/"
    >
      {isIconOnly ? undefined : t('button.privacy-policy')}
    </Button>
  );
}

export function LegalNoticeButton({
  isIconOnly,
  size = 'lg',
  shouldShrink,
}: SocialButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      size={size}
      type="link"
      shouldShrink={shouldShrink}
      href="https://www.electricitymaps.com/legal-notice/"
    >
      {isIconOnly ? undefined : t('button.legal-notice')}
    </Button>
  );
}

export function GitHubButton({
  isIconOnly,
  size = 'lg',
  iconSize = DEFAULT_ICON_SIZE,
  type,
  shouldShrink,
}: SocialButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      size={size}
      type={type}
      shouldShrink={shouldShrink}
      backgroundClasses="bg-[#010409]"
      foregroundClasses="text-white dark:text-white focus-visible:outline-[#010409]"
      href="https://github.com/electricityMaps/electricitymaps-contrib"
      icon={<FaGithub size={iconSize} />}
      onClick={() => {
        trackEvent('Contribute On GitHub Button Clicked');
      }}
    >
      {isIconOnly ? undefined : t('button.github')}
    </Button>
  );
}

export function TwitterButton({
  isIconOnly,
  size = 'lg',
  iconSize = DEFAULT_ICON_SIZE,
  type,
  isShareLink,
  shouldShrink,
}: SocialButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      size={size}
      type={type}
      shouldShrink={shouldShrink}
      backgroundClasses="bg-black"
      foregroundClasses="text-white dark:text-white focus-visible:outline-black"
      href={
        isShareLink
          ? 'https://twitter.com/intent/tweet?url=https://app.electricitymaps.com'
          : undefined
      }
      icon={<FaXTwitter size={iconSize} />}
    >
      {isIconOnly ? undefined : t('button.twitter')}
    </Button>
  );
}

export function FacebookButton({
  isIconOnly,
  size = 'lg',
  iconSize = DEFAULT_ICON_SIZE,
  type,
  isShareLink,
  shouldShrink,
}: SocialButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      size={size}
      type={type}
      shouldShrink={shouldShrink}
      backgroundClasses="bg-[#1877F2]"
      foregroundClasses="text-white dark:text-white focus-visible:outline-[#1877F2]"
      href={
        isShareLink
          ? 'https://facebook.com/sharer/sharer.php?u=https%3A%2F%2Fapp.electricitymaps.com%2F'
          : undefined
      }
      icon={<FaFacebook size={iconSize} />}
    >
      {isIconOnly ? undefined : t('button.facebook')}
    </Button>
  );
}

export function SlackButton({
  isIconOnly,
  size = 'lg',
  iconSize = DEFAULT_ICON_SIZE,
  type,
  isShareLink,
  shouldShrink,
}: SocialButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      size={size}
      type={type}
      shouldShrink={shouldShrink}
      backgroundClasses="bg-[#4a154b]"
      foregroundClasses="text-white dark:text-white focus-visible:outline-[#4a154b]"
      href={isShareLink ? undefined : 'https://slack.electricitymaps.com'}
      icon={<FaSlack size={iconSize} />}
    >
      {isIconOnly ? undefined : t('button.slack')}
    </Button>
  );
}

export function LinkedinButton({
  isIconOnly,
  size = 'lg',
  iconSize = DEFAULT_ICON_SIZE,
  type,
  isShareLink,
  shouldShrink,
}: SocialButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      size={size}
      type={type}
      shouldShrink={shouldShrink}
      backgroundClasses="bg-[#0A66C2]"
      foregroundClasses="text-white dark:text-white focus-visible:outline-[#0A66C2]"
      href={
        isShareLink
          ? 'https://www.linkedin.com/shareArticle?mini=true&url=https://app.electricitymaps.com'
          : 'https://www.linkedin.com/company/electricitymaps/'
      }
      icon={<FaLinkedin size={iconSize} />}
    >
      {isIconOnly ? undefined : t('button.linkedin')}
    </Button>
  );
}

export function FeedbackButton({
  isIconOnly,
  size = 'lg',
  iconSize = DEFAULT_ICON_SIZE,
  type,
  shouldShrink,
}: SocialButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      size={size}
      type={type}
      shouldShrink={shouldShrink}
      href="https://forms.gle/VHaeHzXyGodFKZY18"
      icon={<FaCommentDots size={iconSize} />}
    >
      {isIconOnly ? undefined : t('button.feedback')}
    </Button>
  );
}
