import type { Meta, StoryObj } from '@storybook/react';

import { TwitterButton } from './TwitterButton';

const meta: Meta<typeof TwitterButton> = {
  title: 'Basics/Buttons/Twitter (X)',
  component: TwitterButton,
};

export default meta;
type Story = StoryObj<typeof TwitterButton>;

export const Primary: Story = {
  name: 'Default Twitter (X) Button',
};
