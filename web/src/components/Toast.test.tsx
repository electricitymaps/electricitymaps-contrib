import { ToastProvider } from '@radix-ui/react-toast';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { act, createRef } from 'react';
import { describe, expect, test } from 'vitest';

import { Toast, ToastController, ToastType } from './Toast';

window.HTMLElement.prototype.hasPointerCapture = vi.fn();

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
    const reference = createRef<ToastController>();
    render(
      <ToastProvider>
        <Toast ref={reference} {...props} />
      </ToastProvider>
    );
    act(() => reference.current?.publish());

    expect(screen.getByTestId('toast')).toBeDefined();
  });

  describe('renders by type', () => {
    test('info', () => {
      const reference = createRef<ToastController>();
      render(
        <ToastProvider>
          <Toast ref={reference} {...props} type={ToastType.INFO} />
        </ToastProvider>
      );
      act(() => reference.current?.publish());

      expect(screen.getByTestId('toast').classList.contains('text-blue-800')).toBe(true);
      expect(screen.getByTestId('toast-icon'));
    });

    test('success', () => {
      const reference = createRef<ToastController>();
      render(
        <ToastProvider>
          <Toast ref={reference} {...props} type={ToastType.SUCCESS} />
        </ToastProvider>
      );
      act(() => reference.current?.publish());

      expect(screen.getByTestId('toast').classList.contains('text-emerald-800')).toBe(
        true
      );
      expect(
        screen.getByTestId('toast-icon').classList.contains('lucide-circle-check')
      ).toBe(true);
    });

    test('warning', () => {
      const reference = createRef<ToastController>();
      render(
        <ToastProvider>
          <Toast ref={reference} {...props} type={ToastType.WARNING} />
        </ToastProvider>
      );
      act(() => reference.current?.publish());

      expect(screen.getByTestId('toast').classList.contains('text-amber-700')).toBe(true);
      expect(
        screen.getByTestId('toast-icon').classList.contains('lucide-triangle-alert')
      ).toBe(true);
    });

    test('danger', () => {
      const reference = createRef<ToastController>();
      render(
        <ToastProvider>
          <Toast ref={reference} {...props} type={ToastType.DANGER} />
        </ToastProvider>
      );
      act(() => reference.current?.publish());

      expect(screen.getByTestId('toast').classList.contains('text-red-700')).toBe(true);
      expect(
        screen.getByTestId('toast-icon').classList.contains('lucide-octagon-x')
      ).toBe(true);
    });

    test('default', () => {
      const reference = createRef<ToastController>();
      render(
        <ToastProvider>
          <Toast ref={reference} {...props} />
        </ToastProvider>
      );
      act(() => reference.current?.publish());

      expect(screen.getByTestId('toast').classList.contains('text-blue-800')).toBe(true);
      expect(screen.getByTestId('toast-icon').classList.contains('lucide-info')).toBe(
        true
      );
    });
  });

  test('clicking dismiss closes ', async () => {
    const reference = createRef<ToastController>();
    render(
      <ToastProvider>
        <Toast ref={reference} {...props} />
      </ToastProvider>
    );
    act(() => reference.current?.publish());
    await userEvent.click(screen.getByTestId('toast-dismiss'));

    expect(screen.queryAllByTestId('toast')).toHaveLength(0);
  });
});
