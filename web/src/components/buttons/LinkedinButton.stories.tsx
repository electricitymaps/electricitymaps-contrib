import type { Meta, StoryObj } from '@storybook/react';

import { LinkedinButton } from './LinkedinButton';

const meta: Meta<typeof LinkedinButton> = {
  title: 'Basics/Buttons/Linkedin',
  component: LinkedinButton,
};

export default meta;
type Story = StoryObj<typeof LinkedinButton>;

export const Primary: Story = {
  name: 'Default LinkedIn Button',
};
