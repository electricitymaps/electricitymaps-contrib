import type { Meta, StoryObj } from '@storybook/react';

import { SlackButton } from './SlackButton';

const meta: Meta<typeof SlackButton> = {
  title: 'Basics/Buttons/Slack',
  component: SlackButton,
};

export default meta;
type Story = StoryObj<typeof SlackButton>;

export const Primary: Story = {
  name: 'Default Slack Button',
};
