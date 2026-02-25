import { BrowserRouter, Route, Routes, Link, Navigate, useNavigate, useParams, useSearchParams } from 'react-router'
import { useEffect, useReducer, useState } from 'react'
import './App.css'
import Health from './Health'
import { AccountSwitcher, Login, Signup } from './Auth'
import DetectiveBoard from './DetectiveBoard'
import { EvidenceList, EvidenceSubmitForm, evi_decode } from './Evidence'
import { SubmissionSubmitForm, SubmissionList, subm_decode } from './Submission'
import { CaseList, CaseEditForm, case_decode, case_edit_decode } from './Cases'
import { session, error_msg } from './session'

const Home = () => {
	const [, forced_update] = useReducer(c => c + 1, 0);
	session.listen(forced_update);

	const navigate = useNavigate();
	return (<>
		{/* <p>According to all known laws of aviation...</p>
		{ session.username && <p>Logged in as {session.username}</p> }
		<button onClick={() => navigate('/health')}>Health Check</button>
		{ !session.username && <button onClick={() => navigate('/login')}>Login</button> }
		{ !session.username && <button onClick={() => navigate('/signup')}>Signup</button> }
		{  session.username && <button onClick={() => session.set_creds()}>Logout</button> } */}
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
	const [loadedPath, setLoadedPath] = useState(null)
	const activeUser = session.activeUser

	useEffect(()=>{
		setPhase(0)
		setLoadedPath(null)
		setRes(null)
	}, [activeUser, path])

	const req = () => {
		setPhase(1);
		session.get(path)
			.then(r => {setRes(r.data); setPhase(3); setLoadedPath(path)})
			.catch(err => { setStr(error_msg(err)); setPhase(2); })
	};
	
	console.log(res)
	
	if (phase === 3 && loadedPath===path)
		return then(res, () => { setStr(`Reloading ${msg}...`); setPhase(0); });
	if (phase === 0)
		req();

	return (<>
		<p>{str}</p>
		<button disabled={phase !== 2} onClick={() => { setStr('Retrying...'); req(); }}>Retry</button>
	</>)
}

const UrlList = (local_path, remote_path, Component, props, decoder, title) => (
	<Route path={local_path} exact element={
		<ParamWrap then={(ps, qs) => {
			for (const [key, val] of Object.entries(ps))
				remote_path = remote_path.replace(`<${key}>`, val);

			if (typeof title === 'function')
				title = title(ps, qs);

			return (
				<Retrieve msg="evidence" path={remote_path} then={
					(res, onReload) => (<Component {...props} list={res.map(decoder)} title={title} onReload={onReload}/>)
				}/>
			);
		}}/>
	}/>
);
const chain = (...fns) => x => fns.reduce((mid, fn) => fn(mid), x);

const App = () => {
	const [, forceUpdate] = useReducer(c => c + 1, 0);
	const [frontModules, setModules] = useState([])
	useEffect(() => session.listen(() => forceUpdate()), []);
	useEffect(() => {
		session.get('/api/front-modules')
			.then(res => {
				setModules(res.data.modules)
			})
	}, [session.activeUser]);
	return (<BrowserRouter>
		<div className='w-screen h-screen m-0 px-24 py-24 box-border'>
			<div className='flex flex-col h-full gap-2'>
				<div className='shrink w-full flex flex-row'>
					<div className='flex flex-row grow gap-4 text-xl'>
						<Link to="/home">Home</Link>
						<Link to='/submission/inbox'>Inbox</Link>
						<Link to='/submission/mine'>Submissions</Link>
						{frontModules.includes("COMPLAINANT_CASES")?<Link to='/cases/complainant'>My Cases</Link>:null}
						{frontModules.includes("ASSIGNED_CASES")?<Link to='/cases/list'>Assigned Cases</Link>:null}
					</div>
					<AccountSwitcher />
				</div>
				<div className='grow border-2 border-white p-4'>
					<Routes>
						<Route path="/home" exact element={<Home/>}/>
						<Route path="/health" exact element={<Health/>}/>


						<Route path="/cases/:id/detective-board" exact element={
							<ParamWrap then={ps => (
								<Retrieve msg="evidences" path={`/api/cases/${ps.id}/evidences/`} then={ (evi_list, reload) => (
									<Retrieve msg="board" path={`/api/cases/${ps.id}/detective-board/`} then={ board => (
										<DetectiveBoard
											evi_list={evi_list.map(evi_decode)}
											item_list={board.board_json && board.board_json.items}
											con_list={board.board_json && board.board_json.cons}
											onReload={reload}
										/>
									)}/>
								)}/>
							)}/>
						}/>


						{/* submit pages */}
						<Route path="/login" exact element={<Login/>}/>
						<Route path="/signup" exact element={<Signup/>}/>
						<Route path="/evidence/submit" exact element={<EvidenceSubmitForm/>}/>
						<Route path="/submission/new" exact element={<SubmissionSubmitForm/>}/>
						<Route path="/submission/complaint" exact element={<SubmissionSubmitForm/>}/>
						<Route path="/submission/crime" exact element={<SubmissionSubmitForm/>}/>

						<Route path="/submission/:id/edit" exact element={
							<ParamWrap then={(ps, qs) => (
								<Retrieve msg="submission" path={`/api/submission/${ps.id}/`}
									then={subm => (<SubmissionSubmitForm subm0={{ ...subm.target, submission_type: subm.submission_type }} resubmit={subm.id} returnTo={qs.get('redir')}/>)}
								/>
							)}/>
						}/>

						<Route path="/cases/:id/edit" exact element={
							<ParamWrap then={(ps, qs) => (
								<Retrieve msg="case" path={`/api/cases/${ps.id}/`}
									then={cas => (<CaseEditForm case0={case_edit_decode(cas)} returnTo={qs.get('redir')}/>)}
								/>
							)}/>
						}/>


						{/* list pages */}
						{UrlList('/evidence/list', '/api/evidence/', EvidenceList,{}, evi_decode, 'Evidence List')}
						{UrlList('/submission/mine', '/api/submission/mine/', SubmissionList, 
							{
								create_button:true,
								description:"the submissions you have sent"
							}, 
							subm_decode, 'My Submissions')}
						{UrlList('/submission/inbox', '/api/submission/inbox/', SubmissionList, {
								create_button:false,
								description:"your submission inbox. people are waiting for you to respond"
							}, subm_decode, 'Submission Inbox')}
						{UrlList('/cases/list', '/api/cases/', CaseList, {}, case_decode, 'Case List')}
						{UrlList('/cases/:id/evidences', '/api/cases/<id>/evidences/', EvidenceList, {}, evi_decode, ps => `Evidences of Case ${ps.id}`)}
						{UrlList('/cases/:id/submissions', '/api/cases/<id>/submissions/', SubmissionList, {}, chain(e => e.submission, subm_decode), ps => `Submissions of Case ${ps.id}`)}
						{UrlList('/cases/complainant', '/api/cases/complainant/', CaseList, { safeOnly: true }, case_decode, 'Complainant in')}

						{/* redirect any invalid link to home */}
						<Route path="*" element={<Navigate to="/home" replace />} />
					</Routes>
				</div>
			</div>
		</div>
	</BrowserRouter>)
};

export default App
