/* eslint-disable react-hooks/rules-of-hooks */
import { PrimitiveAtom, useAtom } from 'jotai';
import { ChevronDown, ChevronUp, LucideIcon } from 'lucide-react';
import { useEffect, useState } from 'react';
import { twMerge } from 'tailwind-merge';
import { isTakingScreenshotAtom } from 'utils/state/atoms';

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
  const [, setCollapsedAtom] = isCollapsedAtom ? useAtom(isCollapsedAtom) : [null, null];
  const [isCollapsed, setIsCollapsed] = useState(isCollapsedDefault);
  const [isTakingScreenshot] = useAtom(isTakingScreenshotAtom);

  useEffect(() => {
    if (isTakingScreenshot) {
      setIsCollapsed(false);
      setCollapsedAtom?.(false);
    } else {
      setIsCollapsed(true);
      setCollapsedAtom?.(true);
    }
  }, [isTakingScreenshot, setCollapsedAtom]);

  const handleToggleCollapse = () => {
    onClick?.();

    isCollapsed && onOpen?.();

    setIsCollapsed((previous: boolean) => !previous);

    setCollapsedAtom?.((previous: boolean) => !previous);
  };

  const Icon: LucideIcon = isTopExpanding === isCollapsed ? ChevronUp : ChevronDown;

  return (
    <div className="flex flex-col gap-1.5 py-1">
      <button
        data-test-id="collapse-button"
        onClick={handleToggleCollapse}
        className={twMerge('flex flex-row items-center gap-1.5', className)}
      >
        {icon}
        <h3 className="grow text-left" data-test-id="title">
          {title}
        </h3>
        {badge}
        <Icon
          className="text-black dark:text-white"
          data-test-id={isCollapsed ? 'collapse-down' : 'collapse-up'}
        />
      </button>
      {!isCollapsed && <div>{children}</div>}
    </div>
  );
}
