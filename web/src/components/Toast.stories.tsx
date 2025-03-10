import { ToastProvider } from '@radix-ui/react-toast';
import { Meta, StoryObj } from '@storybook/react';
import { useEffect, useState } from 'react';

import { Toast } from './Toast';

function ToastWrapperComponent() {
  const [showToast, setShowToast] = useState(true);

  useEffect(() => {
    let timerId: string | number | NodeJS.Timeout | undefined;
    if (!showToast) {
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
}

const meta: Meta<typeof Toast> = {
  title: 'Modal/Toast',
  component: Toast,
};

export default meta;
type Story = StoryObj<typeof Toast>;

export const All: Story = {
  render: () => (
    <>
      <p>
        The toast will pop back up when clicked on in the story but not in production.
      </p>
      <br />
      <ToastWrapperComponent />
    </>
  ),
};
