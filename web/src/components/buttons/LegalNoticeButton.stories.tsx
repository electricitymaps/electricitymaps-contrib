import type { Meta, StoryObj } from '@storybook/react';

import { LegalNoticeButton } from './LegalnoticeButton';

const meta: Meta<typeof LegalNoticeButton> = {
  title: 'Basics/Buttons/LegalNotice',
  component: LegalNoticeButton,
};

export default meta;
type Story = StoryObj<typeof LegalNoticeButton>;

export const Primary: Story = {
  name: 'Default Legal Notice Button',
};
