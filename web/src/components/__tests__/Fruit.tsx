import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import fruits from 'mocks/data/fruits.json';
import type ReactRouterDOM from 'react-router-dom';
import Fruit from '../Fruit';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => ({
  ...(await vi.importActual<typeof ReactRouterDOM>('react-router-dom')),
  useNavigate: (): typeof mockNavigate => mockNavigate,
}));

function renderFruit(): void {
  render(<Fruit fruit={fruits[0]} index={0} />);
}

describe('<Fruit />', () => {
  it('renders', () => {
    renderFruit();

    expect(screen.getByText('Photo by')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Matheus Cenali' })).toBeInTheDocument();
    expect(screen.getByText('on')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Unsplash' })).toBeInTheDocument();

    expect(screen.getByText('Apple')).toBeInTheDocument();
  });
  it('redirect to fruit details page on enter', async () => {
    renderFruit();

    screen.getByTestId('FruitCard').focus();
    // No action should be performed
    await userEvent.keyboard('a');
    await userEvent.keyboard('[Enter]');

    expect(mockNavigate).toHaveBeenCalledTimes(1);
    expect(mockNavigate).toHaveBeenCalledWith('apple');
  });
  it('redirect to photographer profile page on image attribute link click', async () => {
    renderFruit();

    await userEvent.click(screen.getByRole('link', { name: 'Matheus Cenali' }));

    expect(mockNavigate).toHaveBeenCalledTimes(0);
  });
});
