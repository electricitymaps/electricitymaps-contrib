import { Capacitor } from '@capacitor/core';
import * as NavigationMenu from '@radix-ui/react-navigation-menu';
import { Button } from 'components/Button';
import Link from 'components/Link';
import { isFAQModalOpenAtom } from 'features/modals/modalAtoms';
import { useSetAtom } from 'jotai';
import { ExternalLink } from 'lucide-react';
import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { twMerge } from 'tailwind-merge';
import trackEvent from 'utils/analytics';
import { TrackEvent } from 'utils/constants';

import Logo, { LogoText } from './Logo';

interface MenuLinkProps {
  href?: string;
  children: React.ReactNode;
  isExternal?: boolean;
  id: string;
  onClick?: () => void;
}

const handleClick = () => {
  trackEvent(TrackEvent.HEADER_LINK_CLICKED, { linkId: 'get-data' });
};

function MenuLink({
  children,
  href,
  isExternal,
  id,
  onClick,
}: MenuLinkProps): JSX.Element {
  const handleClick = useCallback(() => {
    trackEvent(TrackEvent.HEADER_LINK_CLICKED, { linkId: id });
    onClick?.();
  }, [id, onClick]);

  return (
    <NavigationMenu.Item
      asChild
      className="relative my-3 cursor-pointer rounded-md transition-colors hover:bg-zinc-100 dark:hover:bg-black/50"
    >
      <NavigationMenu.Link
        onClick={handleClick}
        href={href}
        target={isExternal ? '_blank' : '_self'}
        className="group px-1 py-2 text-sm lg:px-2 lg:text-base"
      >
        {children}
        {isExternal && (
          <ExternalLink
            size={16}
            className="absolute -right-2 -top-2 text-gray-500 opacity-0 transition-opacity group-hover:opacity-80"
          />
        )}
      </NavigationMenu.Link>
    </NavigationMenu.Item>
  );
}

export default function Header(): JSX.Element {
  const isMobileApp = Capacitor.isNativePlatform();
  const setIsFAQModalOpen = useSetAtom(isFAQModalOpenAtom);
  const { t } = useTranslation();

  const onFAQClick = useCallback(() => {
    setIsFAQModalOpen(true);
  }, [setIsFAQModalOpen]);

  return (
    <header
      className={twMerge(
        'z-40 hidden w-full items-center justify-between bg-white px-4 shadow-[0_4px_6px_-2px_rgba(0,0,0,0.1)] dark:bg-gray-800 dark:shadow-[0_4px_6px_-2px_rgba(0,0,0,0.25)] md:pl-0 md:pr-4 md:pt-[3px]',
        !isMobileApp && 'sm:block md:flex'
      )}
    >
      <Link href="https://electricitymaps.com/?utm_source=app.electricitymaps.com&utm_medium=referral">
        <Logo className="h-12 w-56 fill-black dark:fill-white md:hidden" />
        <LogoText className="-ml-2 hidden h-12 w-48 text-black dark:text-white md:block" />
      </Link>
      <NavigationMenu.Root className="hidden sm:block">
        <NavigationMenu.List className="flex w-full justify-around md:space-x-2">
          <MenuLink id="faq" onClick={onFAQClick}>
            {t('header.faq')}
          </MenuLink>
          <MenuLink
            href="https://www.electricitymaps.com/methodology/?utm_source=app.electricitymaps.com&utm_medium=referral"
            id="methodology"
            isExternal
          >
            {t('header.methodology')}
          </MenuLink>
          <MenuLink
            href="https://www.electricitymaps.com/jobs/?utm_source=app.electricitymaps.com&utm_medium=referral"
            id="jobs"
            isExternal
          >
            {t('header.hiring')}
          </MenuLink>
          <MenuLink
            href="https://electricitymaps.com/open-source/?utm_source=app.electricitymaps.com&utm_medium=referral"
            id="open-source"
            isExternal
          >
            {t('header.open-source')}
          </MenuLink>
          <MenuLink
            href="https://electricitymaps.com/blog/?utm_source=app.electricitymaps.com&utm_medium=referral"
            id="blog"
            isExternal
          >
            {t('header.blog')}
          </MenuLink>
          <Button
            onClick={handleClick}
            backgroundClasses="my-2.5"
            foregroundClasses="text-sm leading-4 lg:leading-5 lg:text-[1rem] px-2 py-0 lg:py-1 lg:px-6"
            href="https://electricitymaps.com/get-our-data?utm_source=app.electricitymaps.com&utm_medium=referral"
          >
            {t('button.api')}
          </Button>
        </NavigationMenu.List>
      </NavigationMenu.Root>
    </header>
  );
}
