/* eslint-disable react-hooks/rules-of-hooks */
import { PrimitiveAtom, useAtom } from 'jotai';
import { useEffect, useState } from 'react';
import { HiChevronDown, HiChevronUp } from 'react-icons/hi2';
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
}) {
  const [collapsedAtom, setCollapsedAtom] = isCollapsedAtom
    ? useAtom(isCollapsedAtom)
    : [null, null];
  const [isCollapsed, setIsCollapsed] = useState(isCollapsedDefault);

  useEffect(() => {
    if (collapsedAtom !== null) {
      setIsCollapsed(collapsedAtom);
    }
  }, [collapsedAtom]);

  const handleToggleCollapse = () => {
    if (onClick != undefined) {
      onClick();
    }

    if (isCollapsed && onOpen != undefined) {
      onOpen();
    }

    setIsCollapsed((previous: boolean) => !previous);
    if (setCollapsedAtom != null) {
      setCollapsedAtom((previous: boolean) => !previous);
    }
  };

  return (
    <div className="flex flex-col py-1">
      <button data-test-id="collapse-button" onClick={handleToggleCollapse}>
        <div
          className={twMerge(
            `flex flex-row items-center justify-between text-sm`,
            className
          )}
        >
          <div className="flex w-2/3 flex-initial flex-row">
            {icon && (
              <div className={`flex items-center justify-center pr-2`}>{icon}</div>
            )}
            <h3 className={`self-center text-left`} data-test-id="title">
              {title}
            </h3>
          </div>
          <div className="flex h-fit flex-row gap-2 text-nowrap">
            {badge}
            <div className="text-xl text-black dark:text-white">
              {isCollapsed ? (
                <div data-test-id="collapse-down">
                  <HiChevronDown />
                </div>
              ) : (
                <div data-test-id="collapse-up">
                  <HiChevronUp />
                </div>
              )}
            </div>
          </div>
        </div>
      </button>
      {!isCollapsed && <div className="pt-1.5">{children}</div>}
    </div>
  );
}
