import { BrowserRouter, Route, Routes, Link, Navigate, useNavigate, useParams, useSearchParams } from 'react-router'
import { useReducer, useState } from 'react'
import './App.css'
import Health from './Health'
import { Login, Signup } from './Auth'
import DetectiveBoard from './DetectiveBoard'
import { EvidenceList, EvidenceSubmitForm, evi_decode } from './Evidence'
import { ComplaintSubmitForm, CrimeSubmitForm, SubmissionSubmitForm, SubmissionList, subm_decode } from './Submission'
import { CaseList, CaseListSafe, case_decode } from './Cases'
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

	const req = () => {
		setPhase(1);
		session.get(path)
			.then(r => {setRes(r.data); setPhase(3);})
			.catch(err => { setStr(error_msg(err)); setPhase(2); })
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

const UrlList = (local_path, remote_path, Component, decoder, title) => (
	<Route path={local_path} exact element={
		<ParamWrap then={(ps, qs) => {
			for (const [key, val] of Object.entries(ps))
				remote_path = remote_path.replace(`<${key}>`, val);

			if (typeof title === 'function')
				title = title(ps, qs);

			return (
				<Retrieve msg="evidence" path={remote_path} then={
					(res, onReload) => (<Component list={res.map(decoder)} title={title} onReload={onReload}/>)
				}/>
			);
		}}/>
	}/>
);

const chain = (...fns) => x => fns.reduce((mid, fn) => fn(mid), x);

const App = () => (
	<BrowserRouter>
		<div className='w-screen h-screen m-0 px-24 py-24 box-border'>
			<div className='flex flex-col h-full gap-2'>
				<div className='shrink w-full flex flex-row'>
					<div className='flex flex-row grow gap-4 text-xl '>
						<Link to="/home">Home</Link>
						<Link to='/submission/inbox'>Inbox</Link>
						<Link to='/submission/mine'>Submissions</Link>
					</div>
					<div className='relative text-xl'>
						<details className='group'>
							<summary className='cursor-pointer select-none underline underline-offset-4 decoration-2 [&::-webkit-details-marker]:hidden'>
								Accounts
							</summary>
							<div className='absolute right-0 z-20 mt-2 flex min-w-40 flex-col gap-2 rounded border border-white/20 bg-[#1f1f1f] p-3 text-left'>
								<Link to='/login' className='hover:underline'>Login</Link>
								<Link to='/signup' className='hover:underline'>Signup</Link>
							</div>
						</details>
					</div>
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
						<Route path="/submission/complaint" exact element={<ComplaintSubmitForm/>}/>
						<Route path="/submission/crime" exact element={<CrimeSubmitForm/>}/>

						<Route path="/submission/:id/edit" exact element={
							<ParamWrap then={(ps, qs) => (
								<Retrieve msg="submission" path={`/api/submission/${ps.id}/`}
									then={subm => (<SubmissionSubmitForm subm0={subm.target} resubmit={subm.id} type={subm.submission_type} returnTo={qs.get('redir')}/>)}
								/>
							)}/>
						}/>


						{/* list pages */}
						{UrlList('/evidence/list', '/api/evidence/', EvidenceList, evi_decode, 'Evidence List')}
						{UrlList('/submission/mine', '/api/submission/mine/', SubmissionList, subm_decode, 'My Submissions')}
						{UrlList('/submission/inbox', '/api/submission/inbox/', SubmissionList, subm_decode, 'Submission Inbox')}
						{UrlList('/cases/list', '/api/cases/', CaseList, case_decode, 'Case List')}
						{UrlList('/cases/:id/evidences', '/api/cases/<id>/evidences/', EvidenceList, evi_decode, ps => `Evidences of Case ${ps.id}`)}
						{UrlList('/cases/:id/submissions', '/api/cases/<id>/submissions/', SubmissionList, chain(e => e.submission, subm_decode), ps => `Submissions of Case ${ps.id}`)}
						{UrlList('/cases/complainant', '/api/cases/complainant/', CaseListSafe, case_decode, 'Complainant in')}

						{/* redirect any invalid link to home */}
						<Route path="*" element={<Navigate to="/home" replace />} />
					</Routes>
				</div>
			</div>
		</div>
	</BrowserRouter>
);

export default App
