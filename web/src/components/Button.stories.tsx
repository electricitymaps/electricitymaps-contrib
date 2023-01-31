import type { Meta, StoryObj } from '@storybook/react';

import { HiMagnifyingGlass } from 'react-icons/hi2';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Basics/Button',
  component: Button,
};

export default meta;
type Story = StoryObj<typeof Button>;

export const All: Story = {
  render: () => (
    <>
      <Button>default button</Button>
      <Button icon={<HiMagnifyingGlass size={18} />}>with icon</Button>
      <Button icon={<HiMagnifyingGlass size={18} />} />
      <Button disabled>disabled</Button>
      <Button background="#44ab60" textColor="#fff">
        custom colors
      </Button>
    </>
  ),
};
