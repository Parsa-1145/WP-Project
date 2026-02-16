import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import session from './session.jsx'

function App() {
	const [str, setStr] = useState('Checking...')
	const [done, setDone] = useState(false);

	useEffect(() => {
			session.get('/health/')
				.then(res => setStr('OK: ' + res.status))
				.catch(err => {
					if (err.response)
						setStr('ERR: ' + err.status);
					else
						setStr('Failed: ' + err.message);
				})
				.finally(() => setDone(true));
		}, [done]);

	return (<>
		<p>{str}</p>
		<button onClick={() => { setStr('Retrying...'); setDone(false); }}>Retry</button>
	</>)
}

export default App
