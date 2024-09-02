/* eslint-disable react-hooks/rules-of-hooks */
import { PrimitiveAtom, useAtom } from 'jotai';
import { ChevronDown, ChevronUp, LucideIcon } from 'lucide-react';
import { useEffect, useState } from 'react';
import { twMerge } from 'tailwind-merge';

export default function Accordion({
  isCollapsedDefault = true,
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
  isCollapsedAtom,
  isTopExpanding = false,
}: {
  isCollapsedDefault?: boolean;
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
  isCollapsedAtom?: PrimitiveAtom<boolean>;
  isTopExpanding?: boolean;
}) {
  const [collapsedAtom, setCollapsedAtom] = isCollapsedAtom
    ? useAtom(isCollapsedAtom)
    : [null, null];
  const [isCollapsed, setIsCollapsed] = useState(isCollapsedDefault);

  useEffect(() => {
    if (collapsedAtom) {
      setIsCollapsed(collapsedAtom);
    }
  }, [collapsedAtom]);

  const handleToggleCollapse = () => {
    onClick?.();

    isCollapsed && onOpen?.();

    setIsCollapsed((previous: boolean) => !previous);

    setCollapsedAtom?.((previous: boolean) => !previous);
  };

  const Icon: LucideIcon = isTopExpanding === isCollapsed ? collapsedIcon : expandedIcon;

  return (
    <div className="flex flex-col gap-1.5 py-1">
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
    </div>
  );
}
