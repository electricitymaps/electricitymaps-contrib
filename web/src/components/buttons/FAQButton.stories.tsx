import type { Meta, StoryObj } from '@storybook/react';

import { FAQButton } from './FAQButton';

const meta: Meta<typeof FAQButton> = {
  title: 'Basics/Buttons/FAQ',
  component: FAQButton,
};

export default meta;
type Story = StoryObj<typeof FAQButton>;

export const Primary: Story = {
  name: 'Default FAQ Button',
};
