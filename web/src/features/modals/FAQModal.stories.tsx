import type { Meta, StoryObj } from '@storybook/react';

import { FAQModalContent } from './FAQModal';

const meta: Meta<typeof FAQModalContent> = {
  title: 'Modal/FAQModal',
  component: FAQModalContent,
};

export default meta;
type Story = StoryObj<typeof FAQModalContent>;

export const Content: Story = {};
