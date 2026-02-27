import '@testing-library/jest-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { Signup, Login, AccountSwitcher } from './Auth';
import { session } from './session';
import toast from 'react-hot-toast';

// Mock the external dependencies
vi.mock('./session', () => ({
    session: {
        post: vi.fn(),
        login: vi.fn(),
        listen: vi.fn(() => vi.fn()),
        accounts: {},
        activeUser: null,
    },
    error_msg_list: vi.fn(),
}));

vi.mock('react-hot-toast', () => ({
    default: {
        error: vi.fn(),
        success: vi.fn(),
    }
}));

// Wrapper to provide React Router context required by useNavigate
const RouterWrapper = ({ children }) => (
    <MemoryRouter>{children}</MemoryRouter>
);

describe('Authentication Components', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders the Signup form with all required fields', () => {
        render(<Signup />, { wrapper: RouterWrapper });
        
        expect(screen.getByText('Sign Up')).toBeInTheDocument();
        expect(screen.getByLabelText('Username')).toBeInTheDocument();
        expect(screen.getByLabelText('Password')).toBeInTheDocument();
        expect(screen.getByLabelText('Confirm')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument();
    });


    it('prevents Signup submission and shows toast error when passwords mismatch', () => {
        render(<Signup />, { wrapper: RouterWrapper });
        
        const passwordInput = screen.getByLabelText('Password');
        const confirmInput = screen.getByLabelText('Confirm');
        const submitBtn = screen.getByRole('button', { name: 'Submit' });

        fireEvent.change(passwordInput, { target: { value: 'securePass123' } });
        fireEvent.change(confirmInput, { target: { value: 'differentPass' } });
        fireEvent.click(submitBtn);

        expect(toast.error).toHaveBeenCalledWith("Passwords don't match");
        expect(session.post).not.toHaveBeenCalled();
    });


    it('calls session.post with correct credentials on Login submit', () => {
        // Setup mock to return a resolved promise to simulate successful network request
        session.post.mockResolvedValueOnce({ data: { access: 'fake-token' } });
        
        render(<Login />, { wrapper: RouterWrapper });
        
        fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'johndoe' } });
        fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'secret' } });
        fireEvent.click(screen.getByRole('button', { name: 'Submit' }));

        expect(session.post).toHaveBeenCalledWith('/api/auth/login/', {
            username: 'johndoe',
            password: 'secret'
        });
    });

    it('displays empty state for AccountSwitcher when no accounts exist', () => {
        render(<AccountSwitcher />, { wrapper: RouterWrapper });
        
        const detailsElement = screen.getByText('Accounts');
        fireEvent.click(detailsElement); // Open the dropdown
        
        expect(screen.getByText('No active accounts.')).toBeInTheDocument();
        expect(screen.getByRole('link', { name: 'Login' })).toBeInTheDocument();
    });
});