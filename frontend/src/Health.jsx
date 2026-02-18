import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import session from './session.jsx'

function App() {
	const [str, setStr] = useState('Checking...')
	const [phase, setPhase] = useState(0);

	const req = () => {
		setPhase(1);
		session.get('/health/')
			.then(res => setStr('OK: ' + res.status))
			.catch(err => {
				if (err.response)
					setStr('ERR: ' + err.status);
				else
					setStr('Failed: ' + err.message);
			})
			.finally(() => setPhase(2));
	};

	if (phase === 0)
		req();

	return (<>
		<p>{str}</p>
		<button disabled={phase !== 2} onClick={() => { setStr('Retrying...'); req(); }}>Retry</button>
	</>)
}

export default App
