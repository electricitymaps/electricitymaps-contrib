import type { Meta, StoryObj } from '@storybook/react';

import { RedditButton } from './RedditButton';

const meta: Meta<typeof RedditButton> = {
  title: 'Basics/Buttons/Reddit',
  component: RedditButton,
};

export default meta;
type Story = StoryObj<typeof RedditButton>;

export const Primary: Story = {
  name: 'Default Reddit Button',
};
