import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router'
import { FormInputField, FormInputChangeFn } from './Forms'
import { session, error_msg_list } from './session.jsx'
import { ChevronDown } from 'lucide-react'
import toast from 'react-hot-toast'

export function Signup() {
	const fields = [
		['text', 'Username', 'username'],
		['text', 'First Name', 'first_name'],
		['text', 'Last Name', 'last_name'],
		['text', 'Email', 'email'],
		['text', 'Phone Number', 'phone_number'],
		['text', 'National ID', 'national_id'],
		['password', 'Password', 'password'],
		['password', 'Confirm', 'pass2'],
	];
	const defaultData = () => {
		const obj = {};
		fields.forEach(e => obj[e[2]] = '');
		return obj;
	}
	const [data, setData] = useState(defaultData);
	const [post, setPost] = useState(false);
	const navigate = useNavigate();

	const submit = () => {
		if (data.password !== data.pass2) {
			toast.error("Passwords don't match");
			return;
		}
		setPost(true);

		session.post('/api/auth/signup/', { ...data, pass2: undefined })
			.then(res => {
				toast.success('Signup successful');
				navigate('/login');
			})
			.catch(err => {
				toast.error(error_msg_list(err));
			})
			.finally(() => setPost(false));
	}

	const ChangeFn = name => FormInputChangeFn(data, setData, 'text', name);
	const Field = (type, name, id) => FormInputField(type, name, data[id], ChangeFn(id), { id: id });
	const FieldArr = arr => Field(arr[0], arr[1], arr[2]);

	return (<>
		<div className='w-full h-full flex flex-col justify-center items-center'>
			<div className='flex flex-col gap-7 bg-(--c-surface) p-4 border-(--c-border) border-1 relative h-min w-80'>
				<h2>
					Sign Up
				</h2>
				<div className='flex flex-col gap-3'>
					{fields.map(FieldArr)}
				</div>
				<button className='btn w-full'onClick={submit} disabled={post}>Submit</button>
			</div>
		</div>
	</>)
}

export function Login() {
	const fields = [
		['text', 'Username', 'username'],
		['password', 'Password', 'password'],
	];
	const defaultData = () => {
		const obj = {};
		fields.forEach(e => obj[e[2]] = '');
		return obj;
	};
	const [data, setData] = useState(defaultData);
	const [post, setPost] = useState(false);
	const navigate = useNavigate();

	const submit = () => {
		setPost(true);

		const req_body = {
			username: data.username,
			password: data.password,
		};

		session.post('/api/auth/login/', req_body)
			.then(res => {
				toast.success('Login successful');
				session.login(data.username, res.data.access);
				navigate('/home');
			})
			.catch(err => {
				toast.error(error_msg_list(err))
			})
			.finally(() => setPost(false));
	}

	const ChangeFn = name => FormInputChangeFn(data, setData, 'text', name);
	const Field = (type, name, id) => FormInputField(type, name, data[id], ChangeFn(id), { id: id });
	const FieldArr = arr => Field(arr[0], arr[1], arr[2]);

	return (<>
		<div className='w-full h-full flex flex-col justify-center items-center'>
			<div className='flex flex-col gap-7 bg-(--c-surface) p-4 border-(--c-border) border-1 relative h-min w-80'>
				<h2>
					Login
				</h2>
				<div className='flex flex-col gap-3'>
					{fields.map(FieldArr)}
				</div>
				<button className='btn w-full'onClick={submit} disabled={post}>Submit</button>
			</div>
		</div>
	</>)
}

export const AccountSwitcher = () => {
	const navigate = useNavigate();
	const [activeUser, setActiveUser] = useState(session.activeUser);
	const [accounts, setAccounts] = useState(() => ({ ...session.accounts }));
	const menuButtonClass = 'w-full cursor-pointer border-1 border-[var(--c-border)] bg-[var(--c-surface-2)] px-2 py-1 text-left text-sm text-[var(--c-text)] hover:bg-[var(--c-primary)] hover:text-black';
	const menuDangerButtonClass = 'w-full cursor-pointer border-1 border-[var(--c-danger)] bg-[var(--c-surface-2)] px-2 py-1 text-left text-sm text-[var(--c-danger)] hover:bg-[var(--c-danger)] hover:text-black';
	const accountButtonBaseClass = 'flex w-full cursor-pointer items-center justify-between border-1 px-2 py-1 text-left text-sm hover:bg-[var(--c-primary)] hover:text-black';

	useEffect(() => {
		const unlisten = session.listen((newActiveUser, newAccounts) => {
			setActiveUser(newActiveUser);
			setAccounts({ ...(newAccounts || {}) });
		});

		return unlisten;
	}, []);

	const usernames = Object.keys(accounts);

	return (
		<div className='relative text-xl w-56 flex justify-center items-center'>
			<details className='group'>
				<summary className='flex min-w-0 cursor-pointer select-none items-center gap-2 border-1 border-[var(--c-border)] bg-[var(--c-surface)] px-3 py-1 text-base hover:bg-[var(--c-surface-2)]'>
					<span className='flex min-w-0 items-baseline gap-1'>
						<span className='underline underline-offset-4 decoration-2 whitespace-nowrap'>
							Accounts
						</span>
						{activeUser && (
							<span className='w-24 truncate text-sm text-[var(--c-text-muted)] group-open:text-[var(--c-text)]'>
								{activeUser}
							</span>
						)}
					</span>
					<ChevronDown className='ml-1 h-3 w-3 text-[var(--c-text-muted)] transition-transform duration-150 group-open:rotate-180' />
				</summary>
				<div className='absolute left-1/2 -translate-x-1/2 z-20 mt-2 flex min-w-52 flex-col gap-2 border-1 border-[var(--c-border)] bg-[var(--c-surface)] p-3 text-left shadow-lg'>
					{usernames.length === 0 ? (
						<>
							<div className='text-sm text-[var(--c-text-muted)]'>No active accounts.</div>
							<Link to='/login' className={menuButtonClass}>
								Login
							</Link>
							<Link to='/signup' className={menuButtonClass}>
								Signup
							</Link>
						</>
					) : (
						<>
							<div className='mb-1 text-sm font-semibold text-[var(--c-text-muted)]'>
								Switch account
							</div>
							<div className='flex flex-col gap-1'>
									{usernames.map(username => (
										<button
											key={username}
											type='button'
											onClick={() => {
												if (username !== activeUser)
													session.switch_account(username);
											}}
											className={`${accountButtonBaseClass} ${
												username === activeUser
													? 'border-[var(--c-primary)] bg-[var(--c-surface)] text-[var(--c-primary)]'
												: 'border-[var(--c-border)] bg-[var(--c-surface-2)] text-[var(--c-text)]'
										}`}
									>
										<span>{username}</span>
										{username === activeUser && (
											<span className='ml-2 text-xs text-[var(--c-primary-strong)]'>
												Active
											</span>
										)}
									</button>
								))}
							</div>
							<div className='my-2 h-px bg-[var(--c-border)]' />
							<button
								type='button'
								onClick={() => navigate('/login')}
								className={menuButtonClass}
							>
								Add account…
							</button>
							<button
								type='button'
								onClick={() => navigate('/signup')}
								className={menuButtonClass}
							>
								Sign Up
							</button>
							<button
								type='button'
								onClick={() => session.logout()}
								className={menuDangerButtonClass}
							>
								Logout
							</button>
						</>
					)}
				</div>
			</details>
		</div>
	);
};
