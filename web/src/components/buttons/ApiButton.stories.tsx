import type { Meta, StoryObj } from '@storybook/react';

import ApiButton from './ApiButton';

const meta: Meta<typeof ApiButton> = {
  title: 'Basics/Buttons/Commercial API',
  component: ApiButton,
};

export default meta;
type Story = StoryObj<typeof ApiButton>;

export const Primary: Story = {
  name: 'Default Commercial API Button',
};

export const Link: Story = {
  name: 'Link Commercial API Button',
  args: {
    type: 'link',
  },
};
