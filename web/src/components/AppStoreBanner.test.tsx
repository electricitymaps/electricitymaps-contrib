import { render, renderHook, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { useAtom } from 'jotai';
import { TestProvider } from 'testing/testUtils';
import { describe, expect, test, vi } from 'vitest';

import { AppStoreBanner, appStoreDismissedAtom, AppStoreURLs } from './AppStoreBanner';

const mocks = vi.hoisted(() => ({
  isMobileWeb: vi.fn(),
  isAndroid: vi.fn(),
  isIphone: vi.fn(),
}));

vi.mock('features/weather-layers/wind-layer/util', () => mocks);

describe('AppStoreBanner', () => {
  beforeEach(() => {
    mocks.isMobileWeb.mockReturnValue(true);
  });
  afterEach(() => {
    vi.restoreAllMocks();
    const { result } = renderHook(() => useAtom(appStoreDismissedAtom));
    result.current[1](false);
  });

  test('renders when isAppBannerDismissed is undefined', () => {
    mocks.isAndroid.mockReturnValue(true);

    render(<AppStoreBanner />);

    expect(screen.getByRole('banner')).toBeDefined();
  });

  test('does not render when isAppBannerDismissed is true', () => {
    render(
      // @ts-expect-error initialValues is not typed correctly
      <TestProvider initialValues={[[appStoreDismissedAtom, true]]}>
        <AppStoreBanner />
      </TestProvider>
    );

    expect(screen.queryAllByRole('banner')).toHaveLength(0);
  });

  test('clicking dismiss sets local storage', async () => {
    mocks.isAndroid.mockReturnValue(true);

    render(<AppStoreBanner />);

    await userEvent.click(screen.getByTestId('dismiss-btn'));

    expect(screen.queryAllByRole('banner')).toHaveLength(0);
  });

  test('clicking cta button sets local storage', async () => {
    mocks.isAndroid.mockReturnValue(true);

    render(<AppStoreBanner />);

    await userEvent.click(screen.getByText('app-banner.cta'));

    expect(screen.queryAllByRole('banner')).toHaveLength(0);
  });

  test('cta href should match on android', () => {
    mocks.isAndroid.mockReturnValue(true);
    mocks.isIphone.mockReturnValue(false);

    render(<AppStoreBanner />);

    const node = screen.getByText('app-banner.cta');
    expect(node.getAttribute('href')).toBe(AppStoreURLs.GOOGLE);
  });

  test('cta href should match on iphone', () => {
    mocks.isAndroid.mockReturnValue(false);
    mocks.isIphone.mockReturnValue(true);

    render(<AppStoreBanner />);

    const node = screen.getByText('app-banner.cta');
    expect(node.getAttribute('href')).toBe(AppStoreURLs.APPLE);
  });

  test('does not render if isMobileWeb is false', () => {
    mocks.isMobileWeb.mockReturnValue(false);

    render(<AppStoreBanner />);

    expect(screen.queryAllByRole('banner')).toHaveLength(0);
  });
});
