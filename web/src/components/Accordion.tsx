import { animated, useSpring } from '@react-spring/web';
import { ChevronDown, ChevronUp, LucideIcon } from 'lucide-react';
import { useState } from 'react';
import { twMerge } from 'tailwind-merge';
import useResizeObserver from 'use-resize-observer';

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
  const [renderChildren, setRenderChildren] = useState(!isCollapsed);
  const handleToggleCollapse = () => {
    onClick?.();

    isCollapsed && onOpen?.();

    setState(!isCollapsed);
  };

  const { ref, height: observerHeight } = useResizeObserver<HTMLDivElement>();

  const spring = useSpring({
    from: { height: 0, rotate: 0 },
    to: { height: observerHeight, rotate: isTopExpanding ? 180 : -180 },
    reverse: isCollapsed,
    config: { tension: 170, friction: 26 },
    onStart: () => {
      !isCollapsed && setRenderChildren(true);
    },
    onRest: () => {
      isCollapsed && setRenderChildren(false);
    },
  });

  const AnimatedIcon = animated<LucideIcon>(isTopExpanding ? ChevronUp : ChevronDown);

  return (
    <div className={`flex flex-col overflow-hidden py-1`}>
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
        <AnimatedIcon
          className="text-black dark:text-white"
          style={{ rotate: spring.rotate.to((r) => `${r}deg`) }}
          data-test-id={isCollapsed ? 'collapse-down' : 'collapse-up'}
        />
      </button>
      <animated.div style={{ height: spring.height }}>
        {/* The div below is used to measure the height of the children
         * DO NOT REMOVE IT
         */}
        {renderChildren && (
          <div ref={ref} className={`${isCollapsed ? 'h-0' : 'h-auto'}`}>
            {children}
          </div>
        )}
      </animated.div>
    </div>
  );
}
