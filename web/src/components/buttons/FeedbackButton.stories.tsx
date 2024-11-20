import type { Meta, StoryObj } from '@storybook/react';

import { FeedbackButton } from './FeedbackButton';

const meta: Meta<typeof FeedbackButton> = {
  title: 'Basics/Buttons/Feedback',
  component: FeedbackButton,
};

export default meta;
type Story = StoryObj<typeof FeedbackButton>;

export const Primary: Story = {
  name: 'Default Feedback Button',
};
