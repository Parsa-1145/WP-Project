import { BrowserRouter, Route, Routes, Link, Navigate } from 'react-router'
import './App.css'
import Health from './Health'

const Home = () => (<>
	<p>According to all known laws of aviation...</p>
	<a href="/health">health check</a>
</>)

const App = () => (<>
	<BrowserRouter>
		<Routes>
			<Route path="/" exact element={<Home/>}/>
			<Route path="/health" exact element={<Health/>}/>
			<Route path="*" element={<Navigate to="/" replace />} />
		</Routes>
	</BrowserRouter>
</>)

export default App
