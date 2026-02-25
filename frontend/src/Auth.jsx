import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router'
import { FormInputField, FormInputChangeFn } from './Forms'
import { session, error_msg_list, error_msg } from './session.jsx'
import { ChevronDown } from 'lucide-react'

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
	const [msgs, setMsgs] = useState([]);
	const navigate = useNavigate();

	const setMsg = msg => setMsgs([msg]);

	const submit = () => {
		if (data.password !== data.pass2) {
			setMsg("ERR: Passwords don't match");
			return;
		}
		setMsg('Awaiting response...');
		setPost(true);

		session.post('/api/auth/signup/', { ...data, pass2: undefined })
			.then(res => {
				setMsg('Signup successful');
				navigate('/login');
			})
			.catch(err => setMsgs(error_msg_list(err)))
			.finally(() => setPost(false));
	}

	const ChangeFn = name => FormInputChangeFn(data, setData, 'text', name);
	const Field = (type, name, id) => FormInputField(type, name, data[id], ChangeFn(id), { id: id });
	const FieldArr = arr => Field(arr[0], arr[1], arr[2]);

	return (<>
		<h1>Signup Page</h1>
		{msgs.map((x, i) => <p key={i}>{x}</p>)}
		<div style={{ maxWidth: '500px', margin: '0 auto' }}>
			{fields.map(FieldArr)}
			<button onClick={submit} disabled={post} style={{ width: '100%' }}>Submit</button>
		</div>
	</>)
}

export function Login() {
	const [user, setUser] = useState('');
	const [pass, setPass] = useState('');
	const [str, setStr] = useState('');
	const [post, setPost] = useState(false);
	const navigate = useNavigate();

	const submit = () => {
		setStr('Awaiting response...');
		setPost(true);

		const req_body = {
			username: user,
			password: pass,
		};

		session.post('/api/auth/login/', req_body)
			.then(res => {
				setStr('Login successful');
				session.login(user, res.data.access);
				navigate('/home');
			})
			.catch(err => setStr(error_msg(err)))
			.finally(() => setPost(false));
	}

	return (<>
		<h1>Login Page</h1>
		{str && <p>{str}</p>}
		<div style={{ display: 'flex', flexDirection: 'column' }}>
			<input type="text" placeholder="Username" value={user} onChange={e => setUser(e.target.value)} />
			<input type="password" placeholder="Password" value={pass} onChange={e => setPass(e.target.value)} />
			<button onClick={submit} disabled={post}>Submit</button>
		</div>
	</>)
}

export const AccountSwitcher = () => {
	const navigate = useNavigate();
	const [activeUser, setActiveUser] = useState(session.activeUser);
	const [accounts, setAccounts] = useState(() => ({ ...session.accounts }));

	useEffect(() => {
		const unlisten = session.listen((newActiveUser, newAccounts) => {
			setActiveUser(newActiveUser);
			setAccounts({ ...(newAccounts || {}) });
		});

		return unlisten;
	}, []);

	const usernames = Object.keys(accounts);

	return (
		<div className='relative text-xl w-56 flex justify-end'>
			<details className='group'>
				<summary className='flex min-w-0 cursor-pointer select-none items-center gap-2 rounded px-3 py-1 text-base hover:bg-white/5'>
					<span className='flex min-w-0 items-baseline gap-1'>
						<span className='underline underline-offset-4 decoration-2 whitespace-nowrap'>
							Accounts
						</span>
						{activeUser && (
							<span className='w-24 truncate text-sm text-white/70 group-open:text-white'>
								{activeUser}
							</span>
						)}
					</span>
					<ChevronDown className='ml-1 h-3 w-3 text-white/70 transition-transform duration-150 group-open:rotate-180' />
				</summary>
				<div className='absolute right-0 z-20 mt-2 flex min-w-52 flex-col gap-2 rounded border border-white/20 bg-[#1f1f1f] p-3 text-left shadow-lg'>
					{usernames.length === 0 ? (
						<>
							<div className='text-sm text-white/70'>No active accounts.</div>
							<Link to='/login' className='hover:underline'>
								Login
							</Link>
							<Link to='/signup' className='hover:underline'>
								Signup
							</Link>
						</>
					) : (
						<>
							<div className='mb-1 text-sm font-semibold text-white/80'>
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
											className={`flex w-full cursor-pointer items-center justify-between rounded px-2 py-1 text-left text-sm hover:bg-white/10 ${
												username === activeUser
													? 'bg-white/10 text-white'
												: 'text-white/80'
										}`}
									>
										<span>{username}</span>
										{username === activeUser && (
											<span className='ml-2 text-xs text-emerald-400'>
												Active
											</span>
										)}
									</button>
								))}
							</div>
							<div className='my-2 h-px bg-white/10' />
							<button
								type='button'
								onClick={() => navigate('/login')}
								className='w-full cursor-pointer rounded px-2 py-1 text-left text-sm text-white/80 hover:bg-white/10'
							>
								Add account…
							</button>
							<button
								type='button'
								onClick={() => navigate('/signup')}
								className='w-full cursor-pointer rounded px-2 py-1 text-left text-sm text-white/80 hover:bg-white/10'
							>
								Sign Up
							</button>
							<button
								type='button'
								onClick={() => session.logout()}
								className='w-full cursor-pointer rounded px-2 py-1 text-left text-sm text-red-300 hover:bg-red-500/20'
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
