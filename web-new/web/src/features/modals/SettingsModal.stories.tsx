import type { Meta, StoryObj } from '@storybook/react';

import { SettingsModalContent } from './SettingsModal';

const meta: Meta<typeof SettingsModalContent> = {
  title: 'Modal/SettingsModal',
  component: SettingsModalContent,
};

export default meta;
type Story = StoryObj<typeof SettingsModalContent>;

export const Content: Story = {};
