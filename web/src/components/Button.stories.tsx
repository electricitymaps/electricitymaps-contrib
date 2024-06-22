import type { Meta, StoryObj } from '@storybook/react';
import { HiMagnifyingGlass } from 'react-icons/hi2';

import { Button } from './Button';

const iconOptions = { noIcon: undefined, icon: <HiMagnifyingGlass size={16} /> };

const meta: Meta<typeof Button> = {
  title: 'Basics/Button',
  component: Button,
  argTypes: {
    children: {
      // Overriding the type to be a string
      type: 'string',
    },
    icon: {
      options: Object.keys(iconOptions),
      mapping: iconOptions,
      control: {
        type: 'inline-radio',
        labels: {
          noIcon: 'No icon',
          icon: 'With icon',
        },
      },
    },
    size: {
      control: {
        type: 'radio',
        options: ['sm', 'md', 'lg'],
        labels: {
          sm: 'Small',
          md: 'Medium',
          lg: 'Large',
        },
      },
    },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  name: 'Default Button',
  args: {
    children: 'Button',
  },
};

export const SmallPrimaryButton: Story = {
  args: {
    size: 'sm',
    type: 'primary',
    children: 'Button',
  },
};

export const MediumPrimaryButton: Story = {
  args: {
    size: 'md',
    type: 'primary',
    children: 'Button',
  },
};

export const LargePrimaryButton: Story = {
  args: {
    size: 'lg',
    type: 'primary',
    children: 'Button',
  },
};

export const LargePrimaryIconButton: Story = {
  storyName: 'Large Button with Icon',
  args: {
    size: 'lg',
    type: 'primary',
    icon: 'icon',
    children: 'Button',
  },
};

export const LargePrimaryIconButtonWithShrink: Story = {
  storyName: 'Large Button with Icon and "shouldShrink"',
  args: {
    size: 'lg',
    type: 'primary',
    icon: 'icon',
    shouldShrink: true,
  },
};

export const LargeLinkButton: Story = {
  storyName: 'Large Button with text and href',
  args: {
    size: 'lg',
    type: 'link',
    children: 'Button',
    href: 'https://electricitymaps.com',
  },
};
