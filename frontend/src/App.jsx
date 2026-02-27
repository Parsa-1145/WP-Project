import { Route, Routes, NavLink, Navigate, useNavigate, useParams, useSearchParams } from 'react-router'
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

const ProfileContent = ({ user, onReload }) => {
	const [submittingBail, setSubmittingBail] = useState(false);
	const [openingPayment, setOpeningPayment] = useState(false);
	const [bailMsg, setBailMsg] = useState('');
	const isArrested = String(user?.status ?? '').toUpperCase() === 'ARRESTED';
	const bailStatus = String(user?.bail_request_status ?? '').toLowerCase();
	const hasPendingBailRequest = bailStatus === 'pending';
	const hasApprovedBailRequest = bailStatus === 'approved' && !!user?.bail_request_id;
	const canSendBailRequest = isArrested && !hasPendingBailRequest && !hasApprovedBailRequest;
	const statusBadgeClass = isArrested
		? 'text-[var(--c-warning)] border-[var(--c-warning)] bg-[var(--c-warning)]/10'
		: 'text-[var(--c-primary)] border-[var(--c-primary)] bg-[var(--c-primary)]/10';
	const bailBadgeClass = bailStatus === 'approved'
		? 'text-[var(--c-primary)] border-[var(--c-primary)] bg-[var(--c-primary)]/10'
		: bailStatus === 'pending'
			? 'text-[var(--c-warning)] border-[var(--c-warning)] bg-[var(--c-warning)]/10'
			: bailStatus === 'rejected'
				? 'text-[var(--c-danger)] border-[var(--c-danger)] bg-[var(--c-danger)]/10'
				: 'text-[var(--c-text-muted)] border-[var(--c-border)] bg-[var(--c-surface-2)]';

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
		<div className='text-left flex flex-col gap-4'>
			<div className='flex flex-row items-center gap-2'>
				<h2 className='m-0 grow'>Profile</h2>
				<button className='btn' onClick={onReload}>reload</button>
			</div>

			<div className='grid gap-3 lg:grid-cols-2'>
				<div className='border-1 border-[var(--c-border)] bg-[var(--c-surface)] p-3 flex flex-col gap-2'>
					<div className='text-xl'>Identity</div>
					<div className='grid gap-2'>
						<div className='border-1 border-dotted border-[var(--c-primary-strong)] p-2 grid grid-cols-[11rem_1fr] gap-2'>
							<div className='text-[var(--c-text-muted)]'>username</div><div>{user.username}</div>
						</div>
						<div className='border-1 border-dotted border-[var(--c-primary-strong)] p-2 grid grid-cols-[11rem_1fr] gap-2'>
							<div className='text-[var(--c-text-muted)]'>first name</div><div>{user.first_name}</div>
						</div>
						<div className='border-1 border-dotted border-[var(--c-primary-strong)] p-2 grid grid-cols-[11rem_1fr] gap-2'>
							<div className='text-[var(--c-text-muted)]'>last name</div><div>{user.last_name}</div>
						</div>
						<div className='border-1 border-dotted border-[var(--c-primary-strong)] p-2 grid grid-cols-[11rem_1fr] gap-2'>
							<div className='text-[var(--c-text-muted)]'>email</div><div className='break-all'>{user.email}</div>
						</div>
						<div className='border-1 border-dotted border-[var(--c-primary-strong)] p-2 grid grid-cols-[11rem_1fr] gap-2'>
							<div className='text-[var(--c-text-muted)]'>national id</div><div>{user.national_id}</div>
						</div>
						<div className='border-1 border-dotted border-[var(--c-primary-strong)] p-2 grid grid-cols-[11rem_1fr] gap-2'>
							<div className='text-[var(--c-text-muted)]'>phone</div><div>{user.phone_number}</div>
						</div>
					</div>
				</div>

				<div className='border-1 border-[var(--c-border)] bg-[var(--c-surface)] p-3 flex flex-col gap-3'>
					<div className='text-xl'>Case / Bail Status</div>
					<div className='flex flex-col gap-2'>
						<div className='border-1 border-dotted border-[var(--c-primary-strong)] p-2 flex flex-row items-center justify-between gap-2'>
							<div className='text-[var(--c-text-muted)]'>status</div>
							<div className={`border-1 px-2 py-0.5 text-sm whitespace-nowrap ${statusBadgeClass}`}>
								{String(user.status || '-')}
							</div>
						</div>
						<div className='border-1 border-dotted border-[var(--c-primary-strong)] p-2 flex flex-row items-center justify-between gap-2'>
							<div className='text-[var(--c-text-muted)]'>bail request status</div>
							<div className={`border-1 px-2 py-0.5 text-sm whitespace-nowrap ${bailBadgeClass}`}>
								{user.bail_request_status ?? '-'}
							</div>
						</div>
						<div className='border-1 border-dotted border-[var(--c-primary-strong)] p-2 grid grid-cols-[11rem_1fr] gap-2'>
							<div className='text-[var(--c-text-muted)]'>has bail request</div><div>{user.has_bail_request ? 'yes' : 'no'}</div>
						</div>
						<div className='border-1 border-dotted border-[var(--c-primary-strong)] p-2 grid grid-cols-[11rem_1fr] gap-2'>
							<div className='text-[var(--c-text-muted)]'>bail request id</div><div>{user.bail_request_id ?? '-'}</div>
						</div>
					</div>
				</div>
			</div>

			<div className='border-1 border-[var(--c-border)] bg-[var(--c-surface)] p-3 flex flex-col gap-2'>
				<div className='text-xl'>Actions</div>
				<div className='flex flex-row flex-wrap gap-2'>
			{canSendBailRequest
				? <button className='btn w-fit' onClick={submitBailRequest} disabled={submittingBail}>Send Bail Request</button>
				: null}
			{hasApprovedBailRequest
				? <button className='btn w-fit' onClick={openPaymentLink} disabled={openingPayment}>Go To Payment Link</button>
				: null}
				</div>
				{bailMsg ? <p className='m-0 text-[var(--c-text-muted)]'>{bailMsg}</p> : null}
			</div>
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

const App = () => {
	const navigate = useNavigate()
	return (
		<div className='w-screen h-screen m-0 px-18 py-12 box-border overflow-hidden'>
				<div className='flex flex-col h-full gap-2 items-center'>
					<div className='shrink w-full flex flex-row justify-center'>
						<div className='grow flex flex-row  gap-4' >
							<Retrieve msg="modules" path={`/api/front-modules/`} then={ ({ modules }) => (<>
								<button className='bg-(--c-primary-strong) text-2xl p-2 text-(--c-surface) hover:bg-(--c-primary)' onClick={() => navigate('/submission/inbox')}>Inbox</button>
								<button className='bg-(--c-primary-strong) text-2xl p-2 text-(--c-surface) hover:bg-(--c-primary)' onClick={() => navigate('/submission/mine')}>Submissions</button>
								<button className='bg-(--c-primary-strong) text-2xl p-2 text-(--c-surface) hover:bg-(--c-primary)' onClick={() => navigate('/most-wanted')}>Most Wanted</button>
								
								{modules.includes("PROFILE")?<button className='bg-(--c-primary-strong) text-2xl p-2 text-(--c-surface) hover:bg-(--c-primary)' onClick={() => navigate('/profile')}>Profile</button>:null}
								{modules.includes("COMPLAINANT_CASES")?<button className='bg-(--c-primary-strong) text-2xl p-2 text-(--c-surface) hover:bg-(--c-primary)' onClick={() => navigate('/cases/complainant')}>My Cases</button>:null}
								{modules.includes("ASSIGNED_CASES")?<button className='bg-(--c-primary-strong) text-2xl p-2 text-(--c-surface) hover:bg-(--c-primary)' onClick={() => navigate('/cases/list')}>Assigned Cases</button>:null}
								{modules.includes("JUDICARY")?<button className='bg-(--c-primary-strong) text-2xl p-2 text-(--c-surface) hover:bg-(--c-primary)' onClick={() => navigate('/judicary')}>Judicary</button>:null}
							</>) } />
						</div>
						<AccountSwitcher />
					</div>
				<div className='grow p-8 overflow-y-scroll'>
						<Routes>
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
