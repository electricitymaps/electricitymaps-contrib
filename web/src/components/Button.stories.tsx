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
        type: 'select',
        options: ['sm', 'md', 'lg'],
        labels: {
          sm: 'Small',
          md: 'Medium',
          lg: 'Large',
        },
      },
    },
    type: {
      control: {
        type: 'select',
        options: ['primary', 'secondary', 'tertiary', 'link'],
        labels: {
          primary: 'Primary',
          secondary: 'Secondary',
          tertiary: 'Tertiary',
          link: 'Link',
        },
      },
    },
  },
  args: {
    icon: 'noIcon',
    children: 'Button',
    size: 'lg',
    type: 'primary',
    shouldShrink: false,
    isDisabled: false,
    href: undefined,
    backgroundClasses: '',
    foregroundClasses: '',
    asDiv: false,
    onClick: () => {},
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  name: 'Default Button',
};

export const SmallPrimaryButton: Story = {
  args: {
    size: 'sm',
  },
};

export const MediumPrimaryButton: Story = {
  args: {
    size: 'md',
  },
};

export const LargePrimaryButton: Story = {};

export const LargePrimaryIconButton: Story = {
  name: 'Large Button with Icon',
  args: {
    icon: 'icon',
  },
};

export const LargePrimaryIconButtonWithShrink: Story = {
  name: 'Large Button with Icon and "shouldShrink"',
  args: {
    icon: 'icon',
    shouldShrink: true,
    children: undefined,
  },
};

export const LargeLinkButton: Story = {
  name: 'Large Button with text and href',
  args: {
    type: 'link',
    href: 'https://electricitymaps.com',
  },
};
