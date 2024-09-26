import { ToastProvider } from '@radix-ui/react-toast';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, expect, test } from 'vitest';

import { Toast, ToastType } from './Toast';

const props = {
  title: 'test',
  description: 'test',
  toastAction: vi.fn(),
  toastActionText: 'action',
  toastClose: vi.fn(),
  duration: 1,
};

describe('Toast', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  test('renders', () => {
    render(
      <ToastProvider>
        <Toast {...props} />
      </ToastProvider>
    );

    expect(screen.getByTestId('toast')).toBeDefined();
  });

  describe('renders by type', () => {
    test('info', () => {
      render(
        <ToastProvider>
          <Toast {...props} type={ToastType.INFO} />
        </ToastProvider>
      );
      expect(screen.getByTestId('toast').classList.contains('text-blue-800')).toBe(true);
      expect(screen.getByTestId('toast-icon'));
    });

    test('success', () => {
      render(
        <ToastProvider>
          <Toast {...props} type={ToastType.SUCCESS} />)
        </ToastProvider>
      );
      expect(screen.getByTestId('toast').classList.contains('text-emerald-800')).toBe(
        true
      );
      expect(
        screen.getByTestId('toast-icon').classList.contains('lucide-circle-check')
      ).toBe(true);
    });

    test('warning', () => {
      render(
        <ToastProvider>
          <Toast {...props} type={ToastType.WARNING} />
        </ToastProvider>
      );
      expect(screen.getByTestId('toast').classList.contains('text-amber-700')).toBe(true);
      expect(
        screen.getByTestId('toast-icon').classList.contains('lucide-triangle-alert')
      ).toBe(true);
    });

    test('danger', () => {
      render(
        <ToastProvider>
          <Toast {...props} type={ToastType.DANGER} />
        </ToastProvider>
      );
      expect(screen.getByTestId('toast').classList.contains('text-red-700')).toBe(true);
      expect(
        screen.getByTestId('toast-icon').classList.contains('lucide-octagon-x')
      ).toBe(true);
    });

    test('default', () => {
      render(
        <ToastProvider>
          <Toast {...props} />
        </ToastProvider>
      );
      expect(screen.getByTestId('toast').classList.contains('text-blue-800')).toBe(true);
      expect(screen.getByTestId('toast-icon').classList.contains('lucide-info')).toBe(
        true
      );
    });
  });

  test('clicking dismiss closes ', async () => {
    render(
      <ToastProvider>
        <Toast {...props} />
      </ToastProvider>
    );

    await userEvent.click(screen.getByTestId('toast-dismiss'));
    expect(screen.queryAllByTestId('toast')).toHaveLength(0);
  });
});
