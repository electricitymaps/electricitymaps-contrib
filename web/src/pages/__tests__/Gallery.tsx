import { screen } from '@testing-library/react';
import GalleryPage from 'pages/Gallery';
import renderWithProviders, { MOBILE_RESOLUTION_HEIGHT, MOBILE_RESOLUTION_WIDTH } from 'testing/testUtils';

describe('<Gallery />', () => {
  it('renders', async () => {
    renderWithProviders(<GalleryPage />);

    await expect(screen.findByRole('img', { name: 'Apple' })).resolves.toHaveAttribute('loading', 'eager');
    expect(screen.getByText('Banana')).toBeInTheDocument();
  });
  it('renders with mobile resolution', async () => {
    window.resizeTo(MOBILE_RESOLUTION_WIDTH, MOBILE_RESOLUTION_HEIGHT);
    renderWithProviders(<GalleryPage />);

    await expect(screen.findByRole('img', { name: 'Grape' })).resolves.toHaveAttribute('loading', 'lazy');
  });
});
