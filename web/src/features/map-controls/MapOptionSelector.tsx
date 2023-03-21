import { useTranslation } from 'translation/translation';
import { Root, Trigger, Portal, Content, Arrow } from '@radix-ui/react-dropdown-menu';

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

  return (
    <Root>
      <Trigger className="pointer-events-auto" data-test-id={testId}>
        {trigger}
      </Trigger>
      <Portal>
        <Content
          className="pointer-events-auto z-50 max-h-[190px] w-[120px] overflow-auto rounded bg-white dark:bg-gray-900"
          sideOffset={5}
          side={isMobile ? 'bottom' : 'left'}
        >
          {children}
          <Arrow className="fill-white dark:fill-gray-900" />
        </Content>
      </Portal>
    </Root>
  );
}
