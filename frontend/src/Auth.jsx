import { useState } from 'react'
import { useNavigate } from 'react-router'
import { FormInputField, FormInputChangeFn } from './Forms'
import session from './session.jsx'

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
			.catch(err => {
				if (err.response)
					setMsgs(Object.entries(err.response.data).map(xy => 'ERR: ' + xy[0] + ' - ' + xy[1]));
				else
					setMsg('ERR: ' + err.message);
			})
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
	const [msg, setMsg] = useState('');
	const [post, setPost] = useState(false);
	const navigate = useNavigate();

	const submit = () => {
		setMsg('Awaiting response...');
		setPost(true);

		const req_body = {
			username: user,
			password: pass,
		};

		session.post('/api/auth/login/', req_body)
			.then(res => {
				setMsg('Login successful');
				session.set_creds(user, res.data.access);
				navigate('/home');
			})
			.catch(err => setMsg('ERR: ' + (err.response? err.response.data.detail: err.message)))
			.finally(() => setPost(false));
	}

	return (<>
		<h1>Login Page</h1>
		{msg && <p>{msg}</p>}
		<div style={{ display: 'flex', flexDirection: 'column' }}>
			<input type="text" placeholder="Username" value={user} onChange={e => setUser(e.target.value)} />
			<input type="password" placeholder="Password" value={pass} onChange={e => setPass(e.target.value)} />
			<button onClick={submit} disabled={post}>Submit</button>
		</div>
	</>)
}
