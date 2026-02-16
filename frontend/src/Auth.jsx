import { useState } from 'react'
import { useNavigate } from 'react-router'
import session from './session.jsx'

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
			<input type="text" placeholder="Password" value={pass} onChange={e => setPass(e.target.value)} />
			<button onClick={submit} disabled={post}>Submit</button>
		</div>
	</>)
}
