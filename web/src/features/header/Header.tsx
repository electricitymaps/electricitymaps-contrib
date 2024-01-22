import { Capacitor } from '@capacitor/core';
import * as NavigationMenu from '@radix-ui/react-navigation-menu';
import { isFAQModalOpenAtom } from 'features/modals/modalAtoms';
import { useSetAtom } from 'jotai';
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
    onClick && onClick();
  };
  return (
    <div className="relative flex py-2">
      <NavigationMenu.Item
        asChild
        className="cursor-pointer rounded-md transition-colors hover:bg-zinc-100 dark:hover:bg-black/50"
      >
        <NavigationMenu.Link
          onClick={handleClick}
          href={href}
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
  return (
    <header
      className={twMerge(
        'z-30 hidden w-full items-center justify-between bg-white px-4 shadow-[0_4px_6px_-2px_rgba(0,0,0,0.1)] md:pr-8 dark:bg-gray-800 dark:shadow-[0_4px_6px_-2px_rgba(0,0,0,0.25)]',
        !isMobileApp && 'sm:block md:flex'
      )}
    >
      <Logo className="h-12 w-56 fill-black dark:fill-white" />
      <NavigationMenu.Root className="hidden sm:block">
        <NavigationMenu.List className="flex w-full justify-around md:space-x-2">
          <MenuLink id="faq" onClick={onFAQClick}>
            FAQ
          </MenuLink>
          <MenuLink
            href="https://www.electricitymaps.com/methodology/?utm_source=app.electricitymaps.com&utm_medium=referral"
            id="methodology"
            isExternal
          >
            Methodology
          </MenuLink>
          <MenuLink
            href="https://www.electricitymaps.com/jobs/?utm_source=app.electricitymaps.com&utm_medium=referral"
            id="jobs"
            isExternal
          >
            We&apos;re hiring!
          </MenuLink>
          <MenuLink
            href="https://electricitymaps.com/open-source/?utm_source=app.electricitymaps.com&utm_medium=referral"
            id="open-source"
            isExternal
          >
            Open Source
          </MenuLink>
          <MenuLink
            href="https://electricitymaps.com/blog/?utm_source=app.electricitymaps.com&utm_medium=referral"
            id="blog"
            isExternal
          >
            Blog
          </MenuLink>
          <MenuLink
            href="https://electricitymaps.com/get-our-data?utm_source=app.electricitymaps.com&utm_medium=referral"
            id="get-data"
            isExternal
          >
            Get our data
          </MenuLink>
        </NavigationMenu.List>
      </NavigationMenu.Root>
    </header>
  );
}
