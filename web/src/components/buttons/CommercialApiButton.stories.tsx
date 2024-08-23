import type { Meta, StoryObj } from '@storybook/react';

import { CommercialApiButton } from './CommercialApiButton';

const meta: Meta<typeof CommercialApiButton> = {
  title: 'Basics/Buttons/Commercial API',
  component: CommercialApiButton,
};

export default meta;
type Story = StoryObj<typeof CommercialApiButton>;

export const Primary: Story = {
  name: 'Default Commercial API Button',
};

export const Link: Story = {
  name: 'Link Commercial API Button',
  args: {
    type: 'link',
  },
};
