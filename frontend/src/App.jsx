import { BrowserRouter, Route, Routes, Link, Navigate, useNavigate } from 'react-router'
import { useReducer } from 'react'
import './App.css'
import Health from './Health'
import { Login, Signup } from './Auth'
import session from './session'

const Home = () => {
	const [, forced_update] = useReducer(c => c + 1, 0);
	session.listen(forced_update);

	const navigate = useNavigate();
	return (<>
		<p>According to all known laws of aviation...</p>
		{ session.username && <p>Logged in as {session.username}</p> }
		<button onClick={() => navigate('/health')}>Health Check</button>
		{ !session.username && <button onClick={() => navigate('/login')}>Login</button> }
		{ !session.username && <button onClick={() => navigate('/signup')}>Signup</button> }
		{  session.username && <button onClick={() => session.set_creds()}>Logout</button> }
	</>)
}

const App = () => {
	return (<BrowserRouter>
		<Link to='/home' style={{ position: 'absolute', left: 0, top: 0 }}>Home</Link>
		<Routes>
			<Route path="/home" exact element={<Home/>}/>
			<Route path="/health" exact element={<Health/>}/>
			<Route path="/login" exact element={<Login/>}/>
			<Route path="/signup" exact element={<Signup/>}/>
			<Route path="*" element={<Navigate to="/home" replace />} />
		</Routes>
	</BrowserRouter>);
}

export default App
