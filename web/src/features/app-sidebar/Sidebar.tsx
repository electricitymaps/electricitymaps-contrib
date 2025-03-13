// These components are modified and scaled-down versions of ShadCN UI's Sidebar components
// https://ui.shadcn.com/docs/components/sidebar
import { Slot } from '@radix-ui/react-slot';
import * as React from 'react';
import { twMerge } from 'tailwind-merge';

const Sidebar = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<'div'> & {
    side?: 'left' | 'right';
    variant?: 'sidebar' | 'floating' | 'inset';
  }
>(({ side = 'left', variant = 'sidebar', className, children, ...props }, reference) => (
  <div
    className="group/sidebar-wrapper absolute left-0 top-0 z-30 flex h-full w-4"
    {...props}
  >
    <div
      ref={reference}
      className="group peer relative hidden h-full md:block"
      data-state={'collapsed'}
      data-collapsible={'icon'}
      data-variant={variant}
      data-side={side}
    >
      <div
        className={twMerge(
          'relative w-[--sidebar-width] bg-transparent transition-[width] duration-200 ease-linear',
          'group-data-[collapsible=offcanvas]:w-0',
          'group-data-[side=right]:rotate-180'
        )}
      />
      <div
        className={twMerge(
          'absolute inset-y-0 z-10 hidden w-[--sidebar-width] transition-[left,right,width] duration-200 ease-linear md:flex',
          side === 'left'
            ? 'left-0 group-data-[collapsible=offcanvas]:left-[calc(var(--sidebar-width)*-1)]'
            : 'right-0 group-data-[collapsible=offcanvas]:right-[calc(var(--sidebar-width)*-1)]',
          'z-20 overflow-hidden  bg-white dark:bg-neutral-900',
          className
        )}
        {...props}
      >
        <div
          data-sidebar="sidebar"
          className="bg-sidebar flex h-full w-full flex-col group-data-[variant=floating]:rounded-lg group-data-[variant=floating]:border group-data-[variant=floating]:border-stroke group-data-[variant=floating]:shadow"
        >
          {children}
        </div>
      </div>
    </div>
  </div>
));
Sidebar.displayName = 'Sidebar';

const SidebarHeader = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<'div'> & { onClick?: () => void }
>(({ className, ...props }, reference) => (
  <div
    ref={reference}
    data-sidebar="header"
    className={twMerge('flex flex-col gap-2 px-2 py-[1.15rem]', className)}
    {...props}
  />
));
SidebarHeader.displayName = 'SidebarHeader';

const SidebarFooter = React.forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
  ({ className, ...props }, reference) => (
    <div
      ref={reference}
      data-sidebar="footer"
      className={twMerge('flex flex-col gap-2 p-2', 'pb-4 pl-4 pr-3', className)}
      {...props}
    />
  )
);
SidebarFooter.displayName = 'SidebarFooter';

const SidebarContent = React.forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
  ({ className, ...props }, reference) => (
    <div
      ref={reference}
      data-sidebar="content"
      className={twMerge(
        'flex min-h-0 flex-1 flex-col gap-2 overflow-auto group-data-[collapsible=icon]:overflow-hidden',

        className
      )}
      {...props}
    />
  )
);
SidebarContent.displayName = 'SidebarContent';

const SidebarGroup = React.forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
  ({ className, ...props }, reference) => (
    <div
      ref={reference}
      data-sidebar="group"
      className={twMerge(
        'relative flex w-full min-w-0 flex-col p-2',
        'px-4 pt-0 transition-all duration-200',
        className
      )}
      {...props}
    />
  )
);
SidebarGroup.displayName = 'SidebarGroup';

const SidebarMenu = React.forwardRef<HTMLUListElement, React.ComponentProps<'ul'>>(
  ({ className, ...props }, reference) => (
    <ul
      ref={reference}
      data-sidebar="menu"
      className={twMerge(
        'flex w-full min-w-0 flex-col gap-1',
        'gap-1 transition-all group-data-[collapsible=icon]:gap-2',
        className
      )}
      {...props}
    />
  )
);
SidebarMenu.displayName = 'SidebarMenu';

const SidebarMenuItem = React.forwardRef<HTMLLIElement, React.ComponentProps<'li'>>(
  ({ className, ...props }, reference) => (
    <li
      ref={reference}
      data-sidebar="menu-item"
      className={twMerge('group/menu-item relative', className)}
      {...props}
    />
  )
);
SidebarMenuItem.displayName = 'SidebarMenuItem';

const SidebarMenuButton = React.forwardRef<
  HTMLButtonElement,
  React.ComponentProps<'button'> & {
    asChild?: boolean;
    isActive?: boolean;
  }
>(({ asChild = false, isActive = false, className, ...props }, reference) => {
  const Comp = asChild ? Slot : 'button';

  return (
    <Comp
      ref={reference}
      data-sidebar="menu-button"
      data-size={'default'}
      data-active={isActive}
      className={twMerge(
        'peer/menu-button hover:text-strong active:text-strong data-[active=true]:text-strong data-[state=open]:hover:bg-hover data-[state=open]:hover:text-strong hover:bg-hover hover:text-strong flex h-8 w-full items-center gap-2 overflow-hidden rounded-md p-2 text-left text-sm outline-none ring-blue-500 transition-[width,height,padding] hover:bg-sunken focus-visible:ring-2 active:bg-sunken disabled:pointer-events-none disabled:opacity-50 group-has-[[data-sidebar=menu-action]]/menu-item:pr-8 aria-disabled:pointer-events-none aria-disabled:opacity-50 data-[active=true]:bg-sunken data-[active=true]:font-medium group-data-[collapsible=icon]:!size-8 group-data-[collapsible=icon]:!p-2 [&>span:last-child]:truncate [&>svg]:size-4 [&>svg]:shrink-0',
        className
      )}
      {...props}
    />
  );
});
SidebarMenuButton.displayName = 'SidebarMenuButton';

export {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
};
