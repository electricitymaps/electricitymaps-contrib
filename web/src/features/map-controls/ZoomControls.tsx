import * as ToggleGroup from '@radix-ui/react-toggle-group';
import { ReactElement, useState } from 'react';

import TooltipWrapper from 'components/tooltips/TooltipWrapper';
import { useTranslation } from 'translation/translation';

export default function ZoomControls(): ReactElement {
  const [value, setValue] = useState('');
  const { __ } = useTranslation();

  return (
    <ToggleGroup.Root
      type="single"
      value={value}
      orientation="vertical"
      onValueChange={(value) => {
        if (value) {
          setValue(value);
        }
      }}
      className="flex flex-col"
    >
      <TooltipWrapper tooltipContent={__('tooltips.zoomIn')}>
        <ToggleGroup.Item
          className="h-8 w-8 rounded rounded-b-none bg-white drop-shadow dark:bg-gray-900"
          value="zoomIn"
        ></ToggleGroup.Item>
      </TooltipWrapper>
      <TooltipWrapper tooltipContent={__('tooltips.zoomOut')}>
        <ToggleGroup.Item
          className="h-8 w-8 rounded  rounded-t-none bg-white drop-shadow dark:bg-gray-900"
          value="zoomOut"
        ></ToggleGroup.Item>
      </TooltipWrapper>
    </ToggleGroup.Root>
  );
}
