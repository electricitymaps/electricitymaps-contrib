import { ChevronDown, ChevronUp, LucideIcon } from 'lucide-react';
import { twMerge } from 'tailwind-merge';

export default function Accordion({
  onClick,
  onOpen,
  badge,
  className,
  icon,
  children,
  title,
  expandedTitle,
  collapsedIcon = ChevronUp,
  expandedIcon = ChevronDown,
  iconClassName,
  iconSize = 24,
  isCollapsed,
  setState,
  isTopExpanding = false,
}: {
  onClick?: () => void;
  onOpen?: () => void;
  badge?: React.ReactNode;
  className?: string;
  icon?: React.ReactNode;
  children?: React.ReactNode;
  title: string;
  expandedTitle?: string;
  collapsedIcon?: LucideIcon;
  expandedIcon?: LucideIcon;
  iconClassName?: string;
  iconSize?: number;
  isCollapsed: boolean;
  setState: (isCollapsed: boolean) => void;
  isTopExpanding?: boolean;
}) {
  const handleToggleCollapse = () => {
    onClick?.();

    isCollapsed && onOpen?.();

    setState(!isCollapsed);
  };

  const Icon: LucideIcon = isTopExpanding === isCollapsed ? collapsedIcon : expandedIcon;

  return (
    <section className="flex flex-col gap-1.5 py-1">
      <button
        data-test-id="collapse-button"
        onClick={handleToggleCollapse}
        className={twMerge('flex flex-row items-center gap-1.5', className)}
      >
        {icon}
        <h3 className="grow text-left" data-test-id="title">
          {(expandedTitle && !isCollapsed ? expandedTitle : title) || title}
        </h3>
        {badge}
        <Icon
          className={twMerge('text-black dark:text-white', iconClassName)}
          data-test-id={isCollapsed ? 'collapse-down' : 'collapse-up'}
          size={iconSize}
        />
      </button>
      {!isCollapsed && <div>{children}</div>}
    </section>
  );
}
