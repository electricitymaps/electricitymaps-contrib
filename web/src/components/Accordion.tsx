import { ChevronDown, ChevronUp } from 'lucide-react';
import { twMerge } from 'tailwind-merge';

export default function Accordion({
  onClick,
  onOpen,
  badge,
  className,
  icon,
  children,
  title,
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
  isCollapsed: boolean;
  setState: (isCollapsed: boolean) => void;
  isTopExpanding?: boolean;
}) {
  const handleToggleCollapse = () => {
    onClick?.();

    isCollapsed && onOpen?.();

    setState(!isCollapsed);
  };

  return (
    <div className="flex flex-col py-1">
      <button
        data-test-id="collapse-button"
        onClick={handleToggleCollapse}
        className={twMerge(
          `flex flex-row items-center justify-between text-sm`,
          className
        )}
      >
        <div className="flex w-2/3 items-center">
          {icon && <div className="pr-2">{icon}</div>}
          <h3 className="self-center" data-test-id="title">
            {title}
          </h3>
        </div>
        <div className="flex h-fit flex-row gap-2 text-nowrap">
          {badge}
          <div
            className="text-xl text-black dark:text-white"
            data-test-id={isCollapsed ? 'collapse-down' : 'collapse-up'}
          >
            {isTopExpanding === isCollapsed ? <ChevronUp /> : <ChevronDown />}
          </div>
        </div>
      </button>
      {!isCollapsed && <div className="pt-1.5">{children}</div>}
    </div>
  );
}
