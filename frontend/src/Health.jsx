import { useState, useEffect } from 'react'
import './App.css'
import { session, error_msg } from './session.jsx'

function App() {
	const [str, setStr] = useState('Checking...')
	const [phase, setPhase] = useState(0);

	const req = () => {
		setPhase(1);
		session.get('/health/')
			.then(res => setStr('OK: ' + res.status))
			.catch(err => setStr(error_msg(err)))
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
