import type { Meta, StoryObj } from '@storybook/react';

import { GithubButton } from './GithubButton';

const meta: Meta<typeof GithubButton> = {
  title: 'Basics/Buttons/Github',
  component: GithubButton,
};

export default meta;
type Story = StoryObj<typeof GithubButton>;

export const Primary: Story = {
  name: 'Default GitHub Button',
};
