/* eslint-disable react-hooks/rules-of-hooks */
import { PrimitiveAtom, useAtom } from 'jotai';
import { ChevronDown, ChevronUp } from 'lucide-react';
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
