import * as NavigationMenu from '@radix-ui/react-navigation-menu';
import trackEvent from 'utils/analytics';
import Logo from './Logo';
import { Capacitor } from '@capacitor/core';
import { twMerge } from 'tailwind-merge';

interface MenuLinkProps {
  href: string;
  children: React.ReactNode;
  active?: boolean;
  id: string;
}
function MenuLink({ children, href, active, id }: MenuLinkProps): JSX.Element {
  return (
    <div className="relative flex py-2 ">
      <NavigationMenu.Item
        asChild
        className="rounded-md transition-colors hover:bg-zinc-100 dark:hover:bg-black/50"
      >
        <NavigationMenu.Link
          onClick={() => trackEvent('HeaderLink Clicked', { linkId: id })}
          active={active}
          href={href}
          className={`px-2 py-2  ${active && 'font-bold'}`}
        >
          {children}
          {active && (
            <div className="absolute left-0 bottom-0 h-[2px] w-full bg-green-500"></div>
          )}
        </NavigationMenu.Link>
      </NavigationMenu.Item>
    </div>
  );
}

export default function Header(): JSX.Element {
  const isMobileApp = Capacitor.isNativePlatform();
  return (
    <header
      className={twMerge(
        'z-30 hidden w-full items-center justify-between bg-white pl-4 pr-8 shadow-[0_4px_6px_-2px_rgba(0,0,0,0.1)] dark:bg-gray-900 dark:shadow-[0_4px_6px_-2px_rgba(0,0,0,0.25)]',
        !isMobileApp && 'sm:flex'
      )}
    >
      <Logo className="h-12 w-56 fill-black dark:fill-white" />
      <NavigationMenu.Root className="hidden md:block">
        <NavigationMenu.List className="flex space-x-2">
          <MenuLink href="/" active id="live">
            Live
          </MenuLink>
          <MenuLink
            href="https://www.electricitymaps.com/jobs/?utm_source=app.electricitymaps.com&utm_medium=referral"
            id="jobs"
          >
            We&apos;re hiring!
          </MenuLink>
          <MenuLink
            href="https://electricitymaps.com/open-source/?utm_source=app.electricitymaps.com&utm_medium=referral"
            id="open-source"
          >
            Open Source
          </MenuLink>
          <MenuLink
            href="https://electricitymaps.com/blog/?utm_source=app.electricitymaps.com&utm_medium=referral"
            id="blog"
          >
            Blog
          </MenuLink>
          <MenuLink
            href="https://electricitymaps.com?utm_source=app.electricitymaps.com&utm_medium=referral"
            id="get-data"
          >
            Get our data
          </MenuLink>
        </NavigationMenu.List>
      </NavigationMenu.Root>
    </header>
  );
}
