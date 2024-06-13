import { ToastProvider } from '@radix-ui/react-toast';
import { Meta, StoryObj } from '@storybook/react';
import { useEffect, useState } from 'react';

import Toast from './Toast';

const meta: Meta<typeof Toast> = {
  title: 'Modals/Toast',
  component: Toast,
};

export default meta;
type Story = StoryObj<typeof Toast>;

export const All: Story = {
  render: () => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const [showToast, setShowToast] = useState(true);

    // eslint-disable-next-line react-hooks/rules-of-hooks
    useEffect(() => {
      let timerId: string | number | NodeJS.Timeout | undefined;
      if (!showToast) {
        // Set a timer to show the toast after 5 seconds
        timerId = setTimeout(() => setShowToast(true), 1000);
      }
      return () => clearTimeout(timerId); // Cleanup the timer
    }, [showToast]);

    return (
      <ToastProvider>
        {showToast && (
          <Toast
            title="Toast Title"
            description="This is a toast description"
            toastAction={() => {
              console.log('Toast action clicked');
              setShowToast(false); // Hide toast when action is clicked
            }}
            toastActionText="Click me"
            toastClose={() => {
              console.log('Toast closed');
              setShowToast(false); // Hide toast when closed
            }}
            duration={Number.POSITIVE_INFINITY}
          />
        )}
      </ToastProvider>
    );
  },
};
