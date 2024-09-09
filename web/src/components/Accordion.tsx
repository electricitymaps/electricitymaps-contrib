import { animated, useSpring } from '@react-spring/web';
import { ChevronRight, LucideIcon } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import useResizeObserver from 'use-resize-observer';

const AnimatedIcon = animated<LucideIcon>(ChevronRight);

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
  const { ref, height: observerHeight } = useResizeObserver<HTMLDivElement>();

  const [spring, api] = useSpring(
    () => ({
      height: isCollapsed ? 0 : observerHeight,
      // eslint-disable-next-line unicorn/no-nested-ternary -- it interferes with prettier
      rotate: isCollapsed ? (isTopExpanding ? -90 : 90) : isTopExpanding ? 90 : -90,
    }),
    [isCollapsed, isTopExpanding, observerHeight]
  );

  const handleToggleCollapse = () => {
    onClick?.();

    isCollapsed && onOpen?.();

    api.start({
      to: {
        height: isCollapsed ? observerHeight : 0,
        // eslint-disable-next-line unicorn/no-nested-ternary -- it interferes with prettier
        rotate: isCollapsed ? (isTopExpanding ? 90 : -90) : isTopExpanding ? -90 : 90,
      },
    });
    setState(!isCollapsed);
  };

  return (
    <div className="flex flex-col overflow-hidden py-1">
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
        <div ref={ref}>{children}</div>
      </animated.div>
    </div>
  );
}
