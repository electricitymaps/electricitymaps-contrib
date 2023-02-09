import type { Meta, StoryObj } from '@storybook/react';

import { InfoModalContent } from './InfoModal';

const meta: Meta<typeof InfoModalContent> = {
  title: 'Modal/InfoModal',
  component: InfoModalContent,
};

export default meta;
type Story = StoryObj<typeof InfoModalContent>;

export const Content: Story = {};
