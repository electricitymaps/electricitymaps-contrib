import type { Meta, StoryObj } from '@storybook/react';

import { PrivacyPolicyButton } from './PrivacyPolicyButton';

const meta: Meta<typeof PrivacyPolicyButton> = {
  title: 'Basics/Buttons/PrivacyPolicy',
  component: PrivacyPolicyButton,
};

export default meta;
type Story = StoryObj<typeof PrivacyPolicyButton>;

export const Primary: Story = {
  name: 'Default PrivacyPolicy Button',
};
