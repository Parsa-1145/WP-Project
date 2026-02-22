import { BrowserRouter, Route, Routes, Link, Navigate, useNavigate, useParams, useSearchParams } from 'react-router'
import { useReducer, useState } from 'react'
import './App.css'
import Health from './Health'
import { Login, Signup } from './Auth'
import DetectiveBoard from './DetectiveBoard'
import { EvidenceList, EvidenceSubmitForm } from './Evidence'
import { ComplaintSubmitForm, CrimeSubmitForm, SubmissionSubmitForm, MySubmissions, InboxSubmissions } from './Submission'
import { CaseList, case_decode } from './Cases'
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

const ParamWrap = ({ then }) => {
	const params = useParams();
	const [searchParams] = useSearchParams();
	return then(params, searchParams);
}
const Retrieve = ({ msg, path, then }) => {
	const [str, setStr] = useState(`Retrieving ${msg}...`)
	const [phase, setPhase] = useState(0);
	const [res, setRes] = useState(null);

	const req = () => {
		setPhase(1);
		session.get(path)
			.then(r => {setRes(r.data); setPhase(3);})
			.catch(err => {
				if (err.response)
					setStr('ERR: ' + err.status);
				else
					setStr('Failed: ' + err.message);
				setPhase(2);
			})
	};

	if (phase === 3)
		return then(res, () => { setStr(`Reloading ${msg}...`); setPhase(0); });
	if (phase === 0)
		req();

	return (<>
		<p>{str}</p>
		<button disabled={phase !== 2} onClick={() => { setStr('Retrying...'); req(); }}>Retry</button>
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
			<Route path="/board" exact element={<DetectiveBoard/>}/>
			<Route path="/evidence/submit" exact element={<EvidenceSubmitForm/>}/>
			<Route path="/evidence/list" exact element={<EvidenceList/>}/>
			<Route path="/submission/complaint" exact element={<ComplaintSubmitForm/>}/>
			<Route path="/submission/crime" exact element={<CrimeSubmitForm/>}/>
			<Route path="/submission/mine" exact element={<MySubmissions/>}/>
			<Route path="/submission/inbox" exact element={<InboxSubmissions/>}/>

			<Route path="/submission/:id/edit" exact element={
				<ParamWrap then={(ps, qs) => (
					<Retrieve
						msg="submission"
						path={`/api/submission/${ps.id}/`}
						then={subm => (<SubmissionSubmitForm subm0={subm.target} resubmit={subm.id} type={subm.submission_type} returnTo={qs.get('redir')}/>)}
					/>
				)}/>
			}/>

			<Route path="/cases/list" exact element={
				<Retrieve msg="cases" path='/api/cases/' then={(res, onReload) => (
					<CaseList case_list={res.map(case_decode)} title='Cases' onReload={onReload}/>
				)}/>
			}/>

			<Route path="*" element={<Navigate to="/home" replace />} />
		</Routes>
	</BrowserRouter>);
}

export default App
