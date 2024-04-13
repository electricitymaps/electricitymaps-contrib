import { PrimitiveAtom, useAtom } from 'jotai';
import { useEffect, useState } from 'react';
import { HiChevronDown, HiChevronUp } from 'react-icons/hi2';
import { twMerge } from 'tailwind-merge';

export default function Accordion({
  isCollapsedDefault = true,
  onClick,
  badge,
  className,
  icon,
  children,
  title,
  isCollapsedAtom,
}: {
  isCollapsedDefault?: boolean;
  onClick?: () => void;
  badge?: React.ReactNode;
  className?: string;
  icon?: React.ReactNode;
  children?: React.ReactNode;
  title: string;
  isCollapsedAtom: PrimitiveAtom<boolean>;
}) {
  const [collapsedAtom, setCollapsedAtom] = useAtom(isCollapsedAtom);
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
    setIsCollapsed((previous: boolean) => !previous);
    if (setCollapsedAtom != null) {
      setCollapsedAtom((previous: boolean) => !previous);
    }
  };

  return (
    <div className="flex flex-col">
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
            <h2 className={`self-center text-left font-semibold`} data-test-id="title">
              {title}
            </h2>
          </div>
          <div className="flex h-fit flex-row gap-2 text-nowrap">
            {badge}
            <div className="text-lg text-black dark:text-white">
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
