import { Capacitor } from '@capacitor/core';
import * as NavigationMenu from '@radix-ui/react-navigation-menu';
import { Button } from 'components/Button';
import { Link } from 'components/Link';
import { isFAQModalOpenAtom } from 'features/modals/modalAtoms';
import { useSetAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { HiOutlineExternalLink } from 'react-icons/hi';
import { twMerge } from 'tailwind-merge';
import trackEvent from 'utils/analytics';

import Logo from './Logo';

interface MenuLinkProps {
  href?: string;
  children: React.ReactNode;
  isExternal?: boolean;
  id: string;
  onClick?: () => void;
}

function MenuLink({
  children,
  href,
  isExternal,
  id,
  onClick,
}: MenuLinkProps): JSX.Element {
  const handleClick = () => {
    trackEvent('HeaderLink Clicked', { linkId: id });
    onClick?.();
  };
  return (
    <div className="relative flex py-3">
      <NavigationMenu.Item
        asChild
        className="cursor-pointer rounded-md transition-colors hover:bg-zinc-100 dark:hover:bg-black/50"
      >
        <NavigationMenu.Link
          onClick={handleClick}
          href={href}
          target={isExternal ? '_blank' : '_self'}
          className="group px-1 py-2 text-base lg:px-2 lg:text-[1rem]"
        >
          {children}
          {isExternal && (
            <div className="absolute bottom-0 top-1 flex w-full justify-end text-gray-400 opacity-0 transition-opacity group-hover:opacity-80 dark:text-gray-600">
              <HiOutlineExternalLink />
            </div>
          )}
        </NavigationMenu.Link>
      </NavigationMenu.Item>
    </div>
  );
}

export default function Header(): JSX.Element {
  const isMobileApp = Capacitor.isNativePlatform();
  const setIsFAQModalOpen = useSetAtom(isFAQModalOpenAtom);
  const onFAQClick = () => {
    setIsFAQModalOpen(true);
  };
  const { t } = useTranslation();
  return (
    <header
      className={twMerge(
        'z-30 hidden w-full items-center justify-between bg-white px-4 shadow-[0_4px_6px_-2px_rgba(0,0,0,0.1)] md:pr-4 dark:bg-gray-800 dark:shadow-[0_4px_6px_-2px_rgba(0,0,0,0.25)]',
        !isMobileApp && 'sm:block md:flex'
      )}
    >
      <Link href="https://electricitymaps.com/?utm_source=app.electricitymaps.com&utm_medium=referral">
        <Logo className="h-12 w-56 fill-black dark:fill-white" />
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
            onClick={() => {
              trackEvent('HeaderLink Clicked', { linkId: 'get-data' });
            }}
            backgroundClasses="my-2.5"
            foregroundClasses="text-base font-normal lg:text-[1rem] py-1 px-6"
            href="https://electricitymaps.com/get-our-data?utm_source=app.electricitymaps.com&utm_medium=referral"
          >
            {t('header.get-data')}
          </Button>
        </NavigationMenu.List>
      </NavigationMenu.Root>
    </header>
  );
}
