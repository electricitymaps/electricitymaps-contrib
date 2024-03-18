import type { Meta, StoryObj } from '@storybook/react';
import { HiMagnifyingGlass } from 'react-icons/hi2';

import { RoundedButton } from './RoundedButton';

const meta: Meta<typeof RoundedButton> = {
  title: 'Basics/RoundedButton',
  component: RoundedButton,
};

export default meta;
type Story = StoryObj<typeof RoundedButton>;

export const All: Story = {
  render: () => (
    <>
      <RoundedButton size="xl" type="primary">
        default xl primary button
      </RoundedButton>
      <RoundedButton size="lg" type="primary">
        default lg primary button
      </RoundedButton>
      <RoundedButton size="sm" type="primary">
        default sm primary button
      </RoundedButton>

      <RoundedButton size="sm" type="primary" backgroundClasses="w-fit">
        default sm primary button with set w-fit
      </RoundedButton>
      <RoundedButton
        size="sm"
        type="primary"
        backgroundClasses="w-fit"
        icon={<HiMagnifyingGlass size={18} />}
      >
        with icon
      </RoundedButton>
      <RoundedButton
        size="sm"
        type="primary"
        backgroundClasses="w-fit"
        icon={<HiMagnifyingGlass size={18} />}
      />

      <RoundedButton size="lg" type="primary" backgroundClasses="w-fit">
        default sm primary button with set w-fit
      </RoundedButton>
      <RoundedButton
        size="lg"
        type="primary"
        backgroundClasses="w-fit"
        icon={<HiMagnifyingGlass size={18} />}
      >
        with icon
      </RoundedButton>
      <RoundedButton
        size="lg"
        type="primary"
        backgroundClasses="w-fit"
        icon={<HiMagnifyingGlass size={18} />}
      />

      <RoundedButton size="xl" type="primary" backgroundClasses="w-fit">
        default sm primary button with set w-fit
      </RoundedButton>
      <RoundedButton
        size="xl"
        type="primary"
        backgroundClasses="w-fit"
        icon={<HiMagnifyingGlass size={18} />}
      >
        with icon
      </RoundedButton>
      <RoundedButton
        size="xl"
        type="primary"
        backgroundClasses="w-fit"
        icon={<HiMagnifyingGlass size={18} />}
      />

      <RoundedButton size="lg" type="primary" disabled>
        disabled
      </RoundedButton>

      <RoundedButton
        size="lg"
        type="primary"
        backgroundClasses="bg-blue-200 dark:bg-blue-200"
        forgroundClasses="text-blue-500 dark:text-blue-500"
        focusOutlineColor="focus:outline-blue-200 focus:dark:outline-blue-200"
      >
        custom colors
      </RoundedButton>

      <RoundedButton size="lg" type="secondary">
        secondary
      </RoundedButton>

      <RoundedButton size="lg" type="secondary-elevated">
        secondary-elevated
      </RoundedButton>

      <RoundedButton size="lg" type="tertiary">
        tertiary
      </RoundedButton>

      <RoundedButton size="lg" type="link">
        link
      </RoundedButton>
    </>
  ),
};
