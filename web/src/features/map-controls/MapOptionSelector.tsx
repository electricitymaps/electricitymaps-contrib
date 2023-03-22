import { useTranslation } from 'translation/translation';
import { Root, Trigger, Portal, Content, Arrow } from '@radix-ui/react-dropdown-menu';
import { useState } from 'react';

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
  const { __ } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const toggleTooltip = () => {
    setIsOpen(!isOpen);
  };
  return (
    <Root open={isOpen} modal={false}>
      <Trigger
        className={isOpen ? 'pointer-events-none' : 'pointer-events-auto'}
        data-test-id={testId}
        onClick={toggleTooltip}
      >
        {trigger}
      </Trigger>
      <Portal>
        <Content
          className="pointer-events-auto z-40 max-h-[190px] w-[120px] overflow-auto rounded bg-white dark:bg-gray-900"
          sideOffset={5}
          side={isMobile ? 'bottom' : 'left'}
          onClick={toggleTooltip}
          onPointerDownOutside={toggleTooltip}
        >
          {children}
          <Arrow className="fill-white dark:fill-gray-900" />
        </Content>
      </Portal>
    </Root>
  );
}
