import type { Meta, StoryObj } from '@storybook/react';

import Badge from './Badge';

const meta: Meta<typeof Badge> = {
  title: 'Basics/Badge',
  component: Badge,
  decorators: [
    (Story) => (
      <div className="flex">
        <Story />
      </div>
    ),
  ],
  argTypes: {
    type: {
      control: {
        type: 'select',
        options: ['default', 'success', 'warning'],
        labels: {
          default: 'Default',
          success: 'Success',
          warning: 'Warning',
        },
      },
    },
  },
  args: {
    pillText: 'Badge',
    type: 'default',
  },
};

export default meta;
type Story = StoryObj<typeof Badge>;

export const Default: Story = {
  name: 'Default Badge',
};

export const Success: Story = {
  name: 'Success Badge',
  args: {
    type: 'success',
  },
};

export const Warning: Story = {
  name: 'Warning Badge',
  args: {
    type: 'warning',
  },
};
