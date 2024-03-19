import type { Meta, StoryObj } from '@storybook/react';
import { HiMagnifyingGlass } from 'react-icons/hi2';

import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Basics/Button',
  component: Button,
};

export default meta;
type Story = StoryObj<typeof Button>;

export const All: Story = {
  render: () => (
    <div className="space-y-2">
      <Button size="xl" type="primary">
        default xl primary button
      </Button>
      <Button size="lg" type="primary">
        default lg primary button
      </Button>
      <Button size="sm" type="primary">
        default sm primary button
      </Button>

      <Button size="sm" type="primary" backgroundClasses="w-fit">
        default sm primary button with set w-fit
      </Button>
      <Button
        size="sm"
        type="primary"
        backgroundClasses="w-fit"
        icon={<HiMagnifyingGlass size={18} />}
      >
        with icon
      </Button>
      <Button
        size="sm"
        type="primary"
        backgroundClasses="w-fit"
        icon={<HiMagnifyingGlass size={18} />}
      />

      <Button size="lg" type="primary" backgroundClasses="w-fit">
        default sm primary button with set w-fit
      </Button>
      <Button
        size="lg"
        type="primary"
        backgroundClasses="w-fit"
        icon={<HiMagnifyingGlass size={18} />}
      >
        with icon
      </Button>
      <Button
        size="lg"
        type="primary"
        backgroundClasses="w-fit"
        icon={<HiMagnifyingGlass size={18} />}
      />

      <Button size="xl" type="primary" backgroundClasses="w-fit">
        default sm primary button with set w-fit
      </Button>
      <Button
        size="xl"
        type="primary"
        backgroundClasses="w-fit"
        icon={<HiMagnifyingGlass size={18} />}
      >
        with icon
      </Button>
      <Button
        size="xl"
        type="primary"
        backgroundClasses="w-fit"
        icon={<HiMagnifyingGlass size={18} />}
      />

      <Button size="lg" type="primary" disabled>
        disabled
      </Button>

      <Button
        size="lg"
        type="primary"
        backgroundClasses="bg-blue-200 dark:bg-blue-200"
        foregroundClasses="text-blue-500 dark:text-blue-500 focus-visible:outline-blue-200 focus-visible:dark:outline-blue-200"
      >
        custom colors
      </Button>

      <Button size="lg" type="secondary">
        secondary
      </Button>

      <Button size="lg" type="secondary-elevated">
        secondary-elevated
      </Button>

      <Button size="lg" type="tertiary">
        tertiary
      </Button>

      <Button size="lg" type="link">
        link lg
      </Button>

      <Button size="sm" type="link" backgroundClasses="w-fit">
        link sm
      </Button>

      <Button size="lg" type="link" backgroundClasses="w-fit">
        link lg
      </Button>

      <Button size="xl" type="link" backgroundClasses="w-fit">
        link xl
      </Button>
    </div>
  ),
};
