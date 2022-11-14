import * as NavigationMenu from '@radix-ui/react-navigation-menu';
import Logo from './Logo';

interface MenuLinkProps {
  href: string;
  children: React.ReactNode;
  active?: boolean;
}
function MenuLink({ children, href, active }: MenuLinkProps): JSX.Element {
  return (
    <div className="relative flex py-2 ">
      <NavigationMenu.Item
        asChild
        className="rounded-md transition-colors hover:bg-zinc-100 dark:hover:bg-black/50"
      >
        <NavigationMenu.Link
          active={active}
          href={href}
          className={`px-2 py-2 text-sm ${active && 'font-bold'}`}
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
  return (
    <header className="z-30 hidden items-center justify-between pl-4 pr-8 shadow-[0_4px_6px_-2px_rgba(0,0,0,0.1)] dark:bg-gray-900 dark:shadow-[0_4px_6px_-2px_rgba(0,0,0,0.25)] md:flex">
      <Logo className="h-12 w-56 fill-black dark:fill-white" />
      <NavigationMenu.Root>
        <NavigationMenu.List className="flex space-x-2">
          <MenuLink href="/" active>
            Live
          </MenuLink>
          <MenuLink href="https://electricitymaps.com/open-source/?utm_source=app.electricitymaps.com&utm_medium=referral">
            We&apos;re hiring!
          </MenuLink>
          <MenuLink href="https://electricitymaps.com/open-source/?utm_source=app.electricitymaps.com&utm_medium=referral">
            Open Source
          </MenuLink>
          <MenuLink href="https://electricitymaps.com/blog/?utm_source=app.electricitymaps.com&utm_medium=referral">
            Blog
          </MenuLink>
          <MenuLink href="https://electricitymaps.com?utm_source=app.electricitymaps.com&utm_medium=referral">
            Get our data
          </MenuLink>
        </NavigationMenu.List>
      </NavigationMenu.Root>
    </header>
  );
}
