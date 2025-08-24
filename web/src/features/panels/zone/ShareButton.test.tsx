import { Share } from '@capacitor/share';
import { ToastProvider } from '@radix-ui/react-toast';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, expect, test, vi } from 'vitest';

import { ShareButton } from './ShareButton';

vi.mock('@capacitor/share', () => ({
  Share: {
    share: vi.fn(),
    canShare: vi.fn(),
  },
}));

const navMocks = vi.hoisted(() => ({
  clipboard: {
    writeText: vi.fn(),
  },
}));

Object.defineProperty(window.navigator, 'clipboard', {
  value: {
    writeText: navMocks.clipboard.writeText,
  },
});

const mocks = vi.hoisted(() => ({
  isMobile: vi.fn(),
  isIos: vi.fn(),
}));

vi.mock('features/weather-layers/wind-layer/util', () => mocks);

describe('ShareButton', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  test('uses Capacitor Share if on mobile and can share', async () => {
    vi.mocked(Share.canShare).mockResolvedValue({ value: true });
    mocks.isMobile.mockReturnValue(true);
    render(
      <ToastProvider>
        <ShareButton />
      </ToastProvider>
    );
    expect(Share.share).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('button'));
    expect(Share.share).toHaveBeenCalled();
  });

  test('does not display error toast on share abort', async () => {
    vi.mocked(Share.canShare).mockResolvedValue({ value: true });
    vi.mocked(Share.share).mockRejectedValue(new Error('AbortError'));
    mocks.isMobile.mockReturnValue(true);
    render(
      <ToastProvider>
        <ShareButton />
      </ToastProvider>
    );
    expect(Share.share).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('button'));
    expect(Share.share).toHaveBeenCalled();
    await userEvent.click(document.body);
    expect(screen.queryAllByTestId('toast')).toHaveLength(0);
  });

  test('does not display error toast on share cancel', async () => {
    vi.mocked(Share.canShare).mockResolvedValue({ value: true });
    vi.mocked(Share.share).mockRejectedValue(new Error('Share canceled'));
    mocks.isMobile.mockReturnValue(true);
    render(
      <ToastProvider>
        <ShareButton />
      </ToastProvider>
    );
    expect(Share.share).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('button'));
    expect(Share.share).toHaveBeenCalled();
    await userEvent.click(document.body);
    expect(screen.queryAllByTestId('toast')).toHaveLength(0);
  });

  test('displays error toast on share error', async () => {
    vi.mocked(Share.canShare).mockResolvedValue({ value: true });
    vi.mocked(Share.share).mockRejectedValue(new Error('Error!'));
    mocks.isMobile.mockReturnValue(true);
    render(
      <ToastProvider>
        <ShareButton />
      </ToastProvider>
    );
    expect(Share.share).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('button'));
    expect(Share.share).toHaveBeenCalled();
    expect(screen.queryAllByTestId('toast')).toHaveLength(1);
  });

  describe('copies to clipboard', () => {
    test('if not on mobile', async () => {
      vi.mocked(Share.canShare).mockResolvedValue({ value: true });
      mocks.isMobile.mockReturnValue(false);
      render(
        <ToastProvider>
          <ShareButton />
        </ToastProvider>
      );
      expect(window.navigator.clipboard.writeText).not.toHaveBeenCalled();
      await userEvent.click(screen.getByRole('button'));
      expect(window.navigator.clipboard.writeText).toHaveBeenCalled();
      expect(Share.share).not.toHaveBeenCalled();
    });
  });
});
