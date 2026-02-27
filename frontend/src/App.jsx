import { Route, Routes, NavLink, Navigate, Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router'
import { useCallback, useEffect, useRef, useState } from 'react'
import './App.css'
import Health from './Health'
import { AccountSwitcher, Login, Signup } from './Auth'
import DetectiveBoard from './DetectiveBoard'
import { EvidenceList, EvidenceSubmitForm, evi_decode } from './Evidence'
import { SubmissionSubmitForm, SubmissionList, subm_decode } from './Submission'
import { CaseList, CaseDetail, CaseEditForm, SuspectCriminalRecordPage, case_decode, case_edit_decode } from './Cases'
import { session, error_msg } from './session'
import MostWantedList from './pages/most-wanted'

const Home = () => {
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

const ProfileContent = ({ user, onReload }) => {
	const [submittingBail, setSubmittingBail] = useState(false);
	const [openingPayment, setOpeningPayment] = useState(false);
	const [bailMsg, setBailMsg] = useState('');
	const isArrested = String(user?.status ?? '').toUpperCase() === 'ARRESTED';
	const bailStatus = String(user?.bail_request_status ?? '').toLowerCase();
	const hasPendingBailRequest = bailStatus === 'pending';
	const hasApprovedBailRequest = bailStatus === 'approved' && !!user?.bail_request_id;
	const canSendBailRequest = isArrested && !hasPendingBailRequest && !hasApprovedBailRequest;

	const submitBailRequest = () => {
		if (submittingBail)
			return;

		setSubmittingBail(true);
		setBailMsg('Submitting bail request...');
		session.post('/api/submission/', {
			submission_type: 'BAIL_REQUEST',
			payload: {},
		})
			.then(() => {
				setBailMsg('Bail request submitted.');
				if (onReload)
					onReload();
			})
				.catch(err => setBailMsg(error_msg(err)))
				.finally(() => setSubmittingBail(false));
	};

	const openPaymentLink = () => {
		if (openingPayment || !user?.bail_request_id)
			return;

		setOpeningPayment(true);
		setBailMsg('Requesting payment link...');
		session.post(`/api/payments/pay/${user.bail_request_id}/`, {})
			.then(res => {
				const paymentUrl = res?.data?.payment_url;
				if (!paymentUrl) {
					setBailMsg('Payment link is not available.');
					return;
				}
				window.location.href = paymentUrl;
			})
			.catch(err => setBailMsg(error_msg(err)))
			.finally(() => setOpeningPayment(false));
	};

	return (
		<div className='text-left flex flex-col gap-2'>
			<h2 className='m-0'>Profile</h2>
			<div>username: {user.username}</div>
			<div>first name: {user.first_name}</div>
			<div>last name: {user.last_name}</div>
			<div>email: {user.email}</div>
			<div>national id: {user.national_id}</div>
			<div>phone: {user.phone_number}</div>
			<div>status: {user.status}</div>
			<div>has bail request: {user.has_bail_request ? 'yes' : 'no'}</div>
			<div>bail request id: {user.bail_request_id ?? '-'}</div>
			<div>bail request status: {user.bail_request_status ?? '-'}</div>
			{canSendBailRequest
				? <button className='btn w-fit' onClick={submitBailRequest} disabled={submittingBail}>Send Bail Request</button>
				: null}
			{hasApprovedBailRequest
				? <button className='btn w-fit' onClick={openPaymentLink} disabled={openingPayment}>Go To Payment Link</button>
				: null}
			{bailMsg ? <p>{bailMsg}</p> : null}
		</div>
	);
};

const Profile = () => (
	<Retrieve msg="profile" path="/api/auth/me/" then={(user, onReload) => (
		<ProfileContent user={user} onReload={onReload} />
	)}/>
)

const ParamWrap = ({ then }) => {
	const params = useParams();
	const [searchParams] = useSearchParams();
	return then(params, searchParams);
}
export const Retrieve = ({ msg, path, then }) => {
	const [str, setStr] = useState(`Retrieving ${msg}...`)
	const [phase, setPhase] = useState(1);
	const [res, setRes] = useState(null);
	const [resPath, setResPath] = useState(null);
	const reqIdRef = useRef(0);

	const req = useCallback((loadingMsg = `Retrieving ${msg}...`) => {
		const reqId = ++reqIdRef.current;
		const requestedPath = path;
		setStr(loadingMsg);
		setPhase(1);
		session.get(requestedPath)
			.then(r => {
				if (reqId !== reqIdRef.current)
					return;
				setRes(r.data);
				setResPath(requestedPath);
				setPhase(3);
			})
			.catch(err => {
				if (reqId !== reqIdRef.current)
					return;
				setStr(error_msg(err));
				setPhase(2);
			})
	}, [msg, path]);

	useEffect(() => {
		req();
	}, [req]);

	useEffect(() => {
		const unlisten = session.listen(() => req());
		return unlisten;
	}, [req]);

	useEffect(() => () => {
		reqIdRef.current += 1;
	}, []);

	if (phase === 3 && path === resPath)
		return then(res, () => req(`Reloading ${msg}...`));

	return (<>
		<p>{str}</p>
		<button disabled={phase !== 2} onClick={() => req('Retrying...')}>Retry</button>
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
const TabLink = ({ to, children }) => (
	<NavLink
		to={to}
		className={({ isActive }) => isActive ? 'tab-link tab-link-active' : 'tab-link'}
	>
		{children}
	</NavLink>
);

const Breadcrumbs = () => {
	const { pathname } = useLocation();
	const crumbs = [{ label: 'Home', to: '/home' }];

	if (pathname === '/' || pathname === '/home')
		return (
			<nav className='breadcrumb-bar' aria-label='Breadcrumb'>
				<span className='breadcrumb-current'>Home</span>
			</nav>
		);

	if (pathname === '/health')
		crumbs.push({ label: 'Health', to: '/health' });
	else if (pathname === '/profile')
		crumbs.push({ label: 'Profile', to: '/profile' });
	else if (pathname === '/login')
		crumbs.push({ label: 'Login', to: '/login' });
	else if (pathname === '/signup')
		crumbs.push({ label: 'Signup', to: '/signup' });
	else if (pathname.startsWith('/submission/')) {
		crumbs.push({ label: 'Submissions', to: '/submission/mine' });
		if (pathname === '/submission/inbox')
			crumbs.push({ label: 'Inbox', to: '/submission/inbox' });
		else if (pathname === '/submission/new')
			crumbs.push({ label: 'New', to: '/submission/new' });
		else {
			const match = pathname.match(/^\/submission\/([^/]+)\/edit$/);
			if (match) {
				crumbs.push({ label: match[1], to: `/submission/${match[1]}/edit` });
				crumbs.push({ label: 'Edit', to: `/submission/${match[1]}/edit` });
			}
		}
	} else if (pathname.startsWith('/cases/')) {
		crumbs.push({ label: 'Cases', to: '/cases/list' });
		if (pathname === '/cases/list')
			null;
		else if (pathname === '/cases/complainant')
			crumbs.push({ label: 'My Cases', to: '/cases/complainant' });
		else {
			const match = pathname.match(/^\/cases\/([^/]+)(?:\/(.*))?$/);
			if (match) {
				const caseId = match[1];
				const tail = match[2] || '';
				crumbs.push({ label: caseId, to: `/cases/${caseId}` });

				if (tail === 'edit')
					crumbs.push({ label: 'Edit', to: `/cases/${caseId}/edit` });
				else if (tail === 'detective-board')
					crumbs.push({ label: 'Detective Board', to: `/cases/${caseId}/detective-board` });
				else if (tail === 'evidences')
					crumbs.push({ label: 'Evidences', to: `/cases/${caseId}/evidences` });
				else if (tail === 'evidences/submit') {
					crumbs.push({ label: 'Evidences', to: `/cases/${caseId}/evidences` });
					crumbs.push({ label: 'Submit', to: `/cases/${caseId}/evidences/submit` });
				} else if (tail === 'submissions')
					crumbs.push({ label: 'Submissions', to: `/cases/${caseId}/submissions` });
				else {
					const recordMatch = tail.match(/^suspects\/([^/]+)\/criminal-record$/);
					if (recordMatch) {
						crumbs.push({ label: recordMatch[1], to: null });
						crumbs.push({ label: 'Criminal Record', to: `/cases/${caseId}/suspects/${recordMatch[1]}/criminal-record` });
					}
				}
			}
		}
	} else if (pathname.startsWith('/evidence/')) {
		crumbs.push({ label: 'Evidence', to: '/evidence/list' });
		if (pathname === '/evidence/submit')
			crumbs.push({ label: 'Submit', to: '/evidence/submit' });
		else if (pathname === '/evidence/list')
			crumbs.push({ label: 'List', to: '/evidence/list' });
	}

	return (
		<nav className='breadcrumb-bar' aria-label='Breadcrumb'>
			{crumbs.map((crumb, idx) => (
				<span key={`${crumb.label}-${idx}`} className='breadcrumb-item'>
					{idx > 0 ? <span className='breadcrumb-sep'>{'>'}</span> : null}
					{idx === crumbs.length - 1 || !crumb.to
						? <span className='breadcrumb-current'>{crumb.label}</span>
						: <Link to={crumb.to} className='breadcrumb-link'>{crumb.label}</Link>}
				</span>
			))}
		</nav>
	);
};

const App = () => {
	return (
		<div className='w-screen h-screen m-0 px-18 py-12 box-border overflow-hidden'>
				<div className='flex flex-col h-full gap-2 '>
					<div className='shrink'>
						<Breadcrumbs />
					</div>
					<div className='shrink w-full flex flex-row'>
						<div className='tab-list grow' role='tablist' aria-label='Main navigation tabs'>
							<Retrieve msg="modules" path={`/api/front-modules/`} then={ ({ modules }) => (<>
							{console.log(modules)}
								<TabLink to="/home">Home</TabLink>
								<TabLink to='/submission/inbox'>Inbox</TabLink>
								<TabLink to='/submission/mine'>Submissions</TabLink>
								<TabLink to='/most-wanted'>Most Wanted</TabLink>
								
								{modules.includes("PROFILE")?<TabLink to='/profile'>Profile</TabLink>:null}
								{modules.includes("COMPLAINANT_CASES")?<TabLink to='/cases/complainant'>My Cases</TabLink>:null}
								{modules.includes("ASSIGNED_CASES")?<TabLink to='/cases/list'>Assigned Cases</TabLink>:null}
								{modules.includes("JUDICARY")?<TabLink to='/judicary'>Judicary</TabLink>:null}
							</>) } />
						</div>
						<AccountSwitcher />
				</div>
				<div className='grow p-8 overflow-y-scroll'>
						<Routes>
							<Route path="/home" exact element={<Home/>}/>
							<Route path="/health" exact element={<Health/>}/>
							<Route path="/profile" exact element={<Profile/>}/>

						<Route path="/cases/:id/detective-board" exact element={
							<ParamWrap then={ps => (
								<Retrieve msg="evidences" path={`/api/cases/${ps.id}/evidences/`} then={ (evi_list, reload) => (
									<Retrieve msg="board" path={`/api/cases/${ps.id}/detective-board/`} then={ board => (
										<DetectiveBoard
											evi_list={evi_list.map(evi_decode)}
											item_list={board.board_json?.items}
											con_list={board.board_json?.cons}
											case_id={ps.id}
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

						<Route path="/submission/new" exact element={
							<Retrieve msg="submission types" path='/api/submission/types/'
								then={({ types }) => (<SubmissionSubmitForm typeList={types} />)}
							/>
						}/>

						<Route path="/submission/:id/edit" exact element={
							<ParamWrap then={(ps, qs) => (
								<Retrieve msg="submission" path={`/api/submission/${ps.id}/`}
									then={subm => (<SubmissionSubmitForm subm0={{ ...subm.target, submission_type: subm.submission_type }} resubmit={subm.id} returnTo={qs.get('redir')}/>)}
								/>
							)}/>
						}/>

						<Route path="/cases/:id/evidences/submit" exact element={
							<ParamWrap then={(ps, qs) => (
								<EvidenceSubmitForm case_id={ps.id}/>
							)}/>
						}/>

						<Route path="/cases/:id/edit" exact element={
							<ParamWrap then={(ps, qs) => (
								<Retrieve msg="case" path={`/api/cases/${ps.id}/`}
									then={cas => (<CaseEditForm case0={case_edit_decode(cas)} returnTo={qs.get('redir')}/>)}
								/>
							)}/>
						}/>
						<Route path="/cases/:id/suspects/:suspect_id/criminal-record" exact element={
							<ParamWrap then={ps => (
								<Retrieve msg="case" path={`/api/cases/${ps.id}/`}
									then={cas => (<SuspectCriminalRecordPage cas={cas} suspectId={ps.suspect_id} />)}
								/>
							)}/>
						}/>
						<Route path="/cases/:id" exact element={
							<ParamWrap then={ps => (
								<Retrieve msg="case" path={`/api/cases/${ps.id}/`}
									then={(cas, onReload) => (<CaseDetail cas={cas} onReload={onReload}/>)}
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
						{UrlList('/most-wanted', '/api/cases/most-wanted/', MostWantedList, {}, x => x, 'Most Wanted')}
						{UrlList('/cases/:id/evidences', '/api/cases/<id>/evidences/', EvidenceList, {}, evi_decode, ps => `Evidences of Case ${ps.id}`)}
						{UrlList('/cases/:id/submissions', '/api/cases/<id>/submissions/', SubmissionList, {}, chain(e => e.submission, subm_decode), ps => `Submissions of Case ${ps.id}`)}
						{UrlList('/cases/complainant', '/api/cases/complainant/', CaseList, { safeOnly: true }, case_decode, 'Complainant in')}
						{UrlList('/judicary', '/api/cases/trial/', CaseList, { canJury: true }, case_decode, 'Complainant in')}
						{/* redirect any invalid link to home */}
						<Route path="*" element={<Navigate to="/home" replace />} />
					</Routes>
				</div>
			</div>
		</div>)
};

export default App
