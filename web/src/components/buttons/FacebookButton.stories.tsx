import type { Meta, StoryObj } from '@storybook/react';

import { FacebookButton } from './FacebookButton';

const meta: Meta<typeof FacebookButton> = {
  title: 'Basics/Buttons/Facebook',
  component: FacebookButton,
};

export default meta;
type Story = StoryObj<typeof FacebookButton>;

export const Primary: Story = {
  name: 'Default Facebook Button',
};
