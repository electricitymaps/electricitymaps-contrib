import { Arrow, Content, Root, Trigger } from '@radix-ui/react-dropdown-menu';
import { useState } from 'react';
import { twMerge } from 'tailwind-merge';

interface MapOptionSelectorProps {
  trigger: React.ReactNode;
  children: React.ReactNode;
  testId?: string;
  isMobile?: boolean;
}
export default function MapOptionSelector({
  trigger,
  testId,
  children,
  isMobile,
}: MapOptionSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const toggleTooltip = () => {
    setIsOpen(!isOpen);
  };
  return (
    <Root open={isOpen} modal={false}>
      <Trigger
        className={twMerge(
          isOpen ? 'pointer-events-none' : 'pointer-events-auto',
          isMobile && 'rounded-full transition duration-200 focus-visible:outline-none '
        )}
        data-test-id={testId}
        onClick={toggleTooltip}
        type={undefined}
      >
        {trigger}
      </Trigger>
      <Content
        className="pointer-events-auto z-50 max-h-[190px] w-[120px] overflow-auto rounded bg-white dark:bg-gray-800"
        sideOffset={isMobile ? -10 : 5}
        side={isMobile ? 'bottom' : 'left'}
        onClick={toggleTooltip}
        onPointerDownOutside={toggleTooltip}
      >
        {children}
        <Arrow className="fill-white dark:fill-gray-900" />
      </Content>
    </Root>
  );
}
