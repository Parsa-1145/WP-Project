import { useState } from 'react'
import { useNavigate } from 'react-router'
import session from './session.jsx'

export function Signup() {
	const [data, setData] = useState({
		username: '',
		first_name: '',
		last_name: '',
		email: '',
		phone_number: '',
		national_id: '',
		password: '',
	});
	const [pass2, setPass2] = useState('');
	const [post, setPost] = useState(false);
	const [msgs, setMsgs] = useState([]);
	const navigate = useNavigate();

	const changeFn = name => e => {
		const data2 = {...data};
		data2[name] = e.target.value;
		setData(data2);
	}
	const setMsg = msg => setMsgs([msg]);

	const submit = () => {
		if (data.password !== pass2) {
			setMsg("ERR: Passwords don't match");
			return;
		}
		setMsg('Awaiting response...');
		setPost(true);

		session.post('/api/auth/signup/', data)
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

	const Field5 = (type, name, id, value, onChange) => (<>
		<label htmlFor={id}>{name}: </label>
		<input id={id} type={type} value={value} onChange={onChange}/>
	</>);
	const Field = (type, name, id) => Field5(type, name, id, data[id], changeFn(id));

	return (<>
		<h1>Signup Page</h1>
		{msgs.map((x, i) => <p key={i}>{x}</p>)}
		<div style={{ display: 'flex', flexDirection: 'column' }}>
			{Field('text', 'Username', 'username')}
			{Field('text', 'First Name', 'first_name')}
			{Field('text', 'Last Name', 'last_name')}
			{Field('text', 'Email', 'email')}
			{Field('text', 'Phone Number', 'phone_number')}
			{Field('text', 'National ID', 'national_id')}
			{Field('password', 'Password', 'password')}
			{Field5('password', 'Confirm Password', 'pass2', pass2, e => setPass2(e.target.value))}
			<button onClick={submit} disabled={post}>Submit</button>
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
