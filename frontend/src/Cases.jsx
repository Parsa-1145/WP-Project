import { useState, useEffect, useContext, useEffectEvent, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router'
import { form_list_decode, form_list_encode, FormInputField, FormInputChangeFn, FormField, GenericList, ListCompactCtx } from './Forms'
import { session, error_msg_list } from './session'
import EvidenceList, { EvidenceSubmitForm, evi_decode } from './Evidence';
import { Retrieve } from './App';
import { useModal } from './modals/ModalHost';
import { SubmissionSubmitForm } from './Submission';
import ConfirmDialog from './modals/ConfirmDialog';
import { formatDate, NormalizationType, normalizeString } from './utils';

// due to case being a keyword, we use cas instead

// type, name, id
const case_fields = [
	['text', 'Title', 'title'],
	['textarea', 'Description', 'description'],
	['datetime', 'Crime Datetime', 'crime_datetime'],
	['text', 'Crime Level', 'crime_level'],
	['text', 'Status', 'status'],
	['text', 'Lead Detective', 'lead_detective'],
	['text', 'Supervisor', 'supervisor'],
	['list !First_Name !Last_Name !Phone .National_ID', 'Witnesses', 'witnesses'],
	['list !First_Name !Last_Name !Phone .National_ID', 'Complainants', 'complainants'],
	['list !First_Name !Last_Name !Phone .National_ID !Link', 'Suspects', 'suspects'],
];
const case_safe_fields = ['id', 'title', 'crime_datetime', 'status', 'complainants'];
const case_edit_fields = ['title', 'description', 'complainants', 'witnesses', 'suspects'];

const case_status_description = {
	"open": "Case is open and the lead detective is actively investigating.",
	"awaiting_investigator": "Case is waiting for a detective to accept it.",
	"awaiting_supervisor" : "Case is waiting for a surgent to supervise it.",
	"interogation": "Suspects are being questioned to clarify key facts.",
	"guilt_assesment": "Evidence is being analyzed to assess responsibility and legal standing.",
	"TRIAL": "Case has moved to court and is currently in trial proceedings.",
	"closed":"Case is finalized with no further active investigation steps."
}
const case_crime_level_name = {
	"L1": "Degree 1",
	"L2": "Degree 2",
	"L3" : "Degree 3",
	"CR": "Critical"
}

export const case_edit_decode = cas => form_list_decode(cas, {
	witnesses   : ['national_id'],
	complainants: ['national_id'],
	suspects    : ['national_id'],
});

export function CaseEditForm({ case0, returnTo }) {
	const defaultData = () => {
		const obj = []
		for (const id of case_edit_fields) obj[id] = case0[id];
		return obj;
	};
	const [data, setData] = useState(defaultData);
	const [post, setPost] = useState(false);
	const [msgs, setMsgs] = useState([]);
	const navigate = useNavigate();
	const setMsg = msg => setMsgs([msg]);

	const submit = () => {
		const req = form_list_encode(data, {
			witnesses: '',
			complainants: '',
			suspects: '',
		});

		const rec_eq = (a, b) => {
			if (typeof a !== typeof b)
				return false;
			if (typeof a !== 'object')
				return a === b;
			const ea = Object.entries(a);
			const eb = Object.entries(b);
			if (ea.length != eb.length)
				return false;
			for (const [k, v] of ea)
				if (!rec_eq(v, b[k]))
					return false;
			return true;
		}

		for (const id of case_edit_fields) {
			if (rec_eq(data[id], case0[id]))
				req[id] = undefined;
		}

		req.witnesses_national_ids = req.witnesses; req.witnesses = undefined;
		req.complainant_national_ids = req.complainants; req.complainants = undefined;

		setPost(true);
		setMsg('Awaiting response...');

		session.patch(`/api/cases/${case0.id}/`, req)
			.then(res => {
				setMsg('Submit successful');
				setData(defaultData());
				if (returnTo) navigate(returnTo);
			})
			.catch(err => setMsgs(error_msg_list(err)))
			.finally(() => setPost(false));
	}

	const ChangeFn = (type, id) => FormInputChangeFn(data, setData, type, id);
	const Field = (type, name, id) => FormInputField(type, name, data[id], ChangeFn(type, id), { id: id });
	const StaticField = (type, name, id) => FormField(type, name, case0[id], { compact: false, id: id });

	return (<>
		<h1>Case Edit</h1>
		{msgs.map((x, i) => <p key={i} style={{ textAlign: 'center' }}>{x}</p>)}
		<div style={{ maxWidth: '500px', margin: '0 auto' }}>
			{case_fields.map(([type, name, id]) =>
				case_edit_fields.includes(id)
					? Field(type, name, id)
					: StaticField(type, name, id)
			)}
			<button onClick={submit} disabled={post} style={{ width: '100%' }}>Submit</button>
		</div>
	</>)
}

export const case_decode = cas => form_list_decode(cas, {
	witnesses   : ['first_name', 'last_name', 'phone_number'],
	complainants: ['first_name', 'last_name', 'phone_number'],
	suspects    : ['first_name', 'last_name', 'phone_number', 'suspect_link'],
});

const getSuspectId = suspect => {
	if (suspect?.id !== undefined && suspect?.id !== null)
		return suspect.id;
	if (suspect?.suspect_id !== undefined && suspect?.suspect_id !== null)
		return suspect.suspect_id;

	const link = String(suspect?.suspect_link ?? '');
	const match = link.match(/\/(\d+)\/?$/);
	return match ? match[1] : null;
};

const getSuspectCriminalRecords = suspect => {
	const records = suspect?.criminal_record ?? suspect?.criminal_records ?? [];
	if (Array.isArray(records))
		return records;
	if (records === null || records === undefined)
		return [];
	return [records];
};

function updateCase(cas) {
	return session.patch(`/api/cases/${cas.id}/`, {
		complainant_national_ids: (cas.complainants || [])
			.map(user => user.national_id)
			.filter(Boolean),
		witnesses_national_ids: (cas.witnesses || [])
			.map(user => user.national_id)
			.filter(Boolean),
	});
}

function UserCard({user, fields=[], onDelete=null}){
	const user_name = [user.first_name, user.last_name].filter(Boolean).join(' ') || user.national_id;
	return(
		<>
			<div className='user-card'>
				<div className='grow'>
					<div className='text-2xl p-0 m-0'>{user_name}</div>
					<div className='text-lg m-0 '>national id: <span className=''>{user.national_id}</span></div>
					<div className='m-0 p-0'>phone: <span className=''>{user.phone_number}</span></div>
				</div>
				<div className='flex flex-row gap-2 justify-end'>
					<button className='btn' onClick={() => onDelete && onDelete(user)}>delete</button>
				</div>
			</div>
		</>
	)
}

function SuspectCard({user, your_role, fields=[], onScoreUpdate, onMarkArrested, onViewCriminalRecord, cas}){
	const user_name = [user.first_name, user.last_name].filter(Boolean).join(' ') || user.national_id;
	const status = (user.status || '').toLowerCase().replace(/_/g, ' ');
	const role = (your_role || '').toLowerCase();
	const currentScore = role === 'detective'
		? user.detective_score
		: user.supervisor_score;
	const scoreInput = useRef(null)

	const submitScoreUpdate = () => {
		if (!onScoreUpdate)
			return;

		const parsed = Number(scoreInput.current.value);
		if (Number.isNaN(parsed))
			return;

		onScoreUpdate(user, parsed);
	};

	return(
		<>
			<div className='user-card'>
				<div className='grow'>
					<div className='text-2xl p-0 m-0'>{user_name}</div>
					<div>status: {status}</div>
					<div>detective score: {user.detective_score}</div>
					<div>supervisor score: {user.supervisor_score}</div>
				</div>
				<div className='flex flex-col gap-1'>
					{onViewCriminalRecord
						? <button className='btn w-full text-base' onClick={() => onViewCriminalRecord(user)}>criminal record</button>
						: null}
					{(role=="detective" || role=="supervisor") && cas.status=="interogation" ? (
						<>
							{status === 'wanted' && onMarkArrested
								? <button className='btn w-full text-base' onClick={() => onMarkArrested(user)}>mark arrested</button>
								: null}
							<div className='flex flex-row gap-1'>
								<input
									placeholder='score'
									defaultValue={currentScore}
									className='input grow'
									ref={scoreInput}
								/>
								<button className='btn' onClick={submitScoreUpdate}>ok</button>
							</div>
						</>
					) : null}
				</div>
			</div>
		</>
	)
	}

function CriminalRecordCard({rec}){
	console.log(rec)
	return(
		<>
			<div className='border-1 p-2'>
				<h1>
					{rec.title}
				</h1>
				<h3>
					{rec.description}
				</h3>
				<h2>
					Case Status: {normalizeString(rec.status)}
				</h2>
				<h2>
					Crime Date: {formatDate(rec.crime_datetime)}
				</h2>
			</div>
		</>
	)
}

export function SuspectCriminalRecordPage({ cas, suspectId }) {
	const navigate = useNavigate();
	const suspects = cas?.suspects || [];
	const suspect = suspects.find(sus => String(getSuspectId(sus)) === String(suspectId));
	const records = getSuspectCriminalRecords(suspect);
	const suspectName = suspect
		? [suspect.first_name, suspect.last_name].filter(Boolean).join(' ') || suspect.national_id || suspectId
		: suspectId;

	return (
		<div className='text-left flex flex-col gap-4'>
			<div className='flex flex-row items-center gap-2'>
				<button className='btn' onClick={() => navigate(`/cases/${cas.id}`)}>Back</button>
				<h2 className='m-0'>Criminal Record - {suspectName}</h2>
			</div>
			<div className='flex flex-col gap-2'>
				{records.map((rec, idx) => (
					<CriminalRecordCard key={idx} rec={rec}/>
				))}
			</div>
		</div>
	);
}


function InvestigationApprovalModal({ caseId, onClose, onSubmitted }) {
	return (
		<div style={{ width: 'min(40rem, 100%)' }}>
			<div className='flex flex-row items-center justify-between mb-2'>
				<h2 className='m-0'>Investigation Approval</h2>
				<button className='btn whitespace-nowrap' onClick={onClose}>close</button>
			</div>
			<SubmissionSubmitForm
				submissionType='INVESTIGATION_APPROVAL'
				fixedFields={{ case: caseId }}
				subm0={{
					suggested_suspects: [],
				}}
				onSubmitted={onSubmitted}
			/>
		</div>
	);
}

function EvidenceCreateModal({ caseId, onClose, onSubmitted }) {
	return (
		<div style={{ width: 'min(40rem, 100%)' }}>
			{/* <div className='flex flex-row items-center justify-between mb-2'>
				<h2 className='m-0'>Create Evidence</h2>
				<button className='btn whitespace-nowrap' onClick={onClose}>close</button>
			</div> */}
			<EvidenceSubmitForm
				case_id={caseId}
				onSubmitted={onSubmitted}
			/>
		</div>
	);
}

function TitledBox({title, className, children}){
	return(
		<div className=''>
				<div className='mb-2 bg-[var(--c-primary)] text-black text-2xl p-1 w-min'>
					{title}
				</div>
			<div className={className + " p-2 border-1 border-[var(--c-primary)]"}>
				{children}
			</div>
		</div>
	)
}

export function CaseDetail({ cas, onReload }) {
	const [newComplainantNid, setNewComplainantNid] = useState('');
	const [newWitnessNid, setNewWitnessNid] = useState('');
	const modalApi = useModal()

	const [saving, setSaving] = useState(false);
	const [msgs, setMsgs] = useState([]);
	const navigate = useNavigate();

	const complainants = cas.complainants || [];
	const witnesses = cas.witnesses || [];

	// useEffect(() => {
	// 	setcas(cloneCase(cas));
	// 	setNewComplainantNid('');
	// 	setNewWitnessNid('');
	// }, [cas]);

	const submitCaseUpdate = ({ nextCase, pendingMsg, successMsg, onSuccess }) => {
		setSaving(true);
		setMsgs([pendingMsg]);
		updateCase(nextCase)
			.then(() => {
				if (onSuccess) onSuccess();
				setMsgs([successMsg]);
				if (onReload) onReload();
			})
			.catch(err => setMsgs(error_msg_list(err)))
			.finally(() => setSaving(false));
	};

	const submitSuspectUpdate = ({ suspectUpdate, pendingMsg, successMsg, onSuccess }) => {
		setSaving(true);
		setMsgs([pendingMsg]);
		session.patch(`/api/cases/${cas.id}/`, {
			suspects: [suspectUpdate],
		})
			.then(() => {
				if (onSuccess) onSuccess();
				setMsgs([successMsg]);
				if (onReload) onReload();
			})
			.catch(err => setMsgs(error_msg_list(err)))
			.finally(() => setSaving(false));
	};

	const removeComplainant = user => {
		if (saving)
			return;

		const complainantsNext = complainants.filter(
			ent => (ent.id !== undefined && user.id !== undefined)
				? ent.id !== user.id
				: ent.national_id !== user.national_id
		);

		submitCaseUpdate({
			nextCase: { ...cas, complainants: complainantsNext },
			pendingMsg: 'Updating complainants...',
			successMsg: 'Complainant removed successfully.',
		});
	};

	const addComplainant = () => {
		if (saving)
			return;

		const nationalId = newComplainantNid.trim();
		if (!nationalId) {
			setMsgs(['Please enter a national id.']);
			return;
		}

		if (complainants.some(ent => ent.national_id === nationalId)) {
			setMsgs(['This complainant is already in the list.']);
			return;
		}

		const complainantsNext = [...complainants, {
			first_name: '',
			last_name: '',
			national_id: nationalId,
			phone_number: '',
		}];

		submitCaseUpdate({
			nextCase: { ...cas, complainants: complainantsNext },
			pendingMsg: 'Adding complainant...',
			successMsg: 'Complainant added successfully.',
			onSuccess: () => setNewComplainantNid(''),
		});
	};

	const removeWitness = user => {
		if (saving)
			return;

		const witnessesNext = witnesses.filter(
			ent => (ent.id !== undefined && user.id !== undefined)
				? ent.id !== user.id
				: ent.national_id !== user.national_id
		);

		submitCaseUpdate({
			nextCase: { ...cas, witnesses: witnessesNext },
			pendingMsg: 'Updating witnesses...',
			successMsg: 'Witness removed successfully.',
		});
	};

	const addWitness = () => {
		if (saving)
			return;

		const nationalId = newWitnessNid.trim();
		if (!nationalId) {
			setMsgs(['Please enter a national id.']);
			return;
		}

		if (witnesses.some(ent => ent.national_id === nationalId)) {
			setMsgs(['This witness is already in the list.']);
			return;
		}

		const witnessesNext = [...witnesses, {
			first_name: '',
			last_name: '',
			national_id: nationalId,
			phone_number: '',
		}];

		submitCaseUpdate({
			nextCase: { ...cas, witnesses: witnessesNext },
			pendingMsg: 'Adding witness...',
			successMsg: 'Witness added successfully.',
			onSuccess: () => setNewWitnessNid(''),
		});
	};

	const markSuspectArrested = suspect => {
		if (saving)
			return;

		if (!suspect?.suspect_link) {
			setMsgs(['Invalid suspect link.']);
			return;
		}

		submitSuspectUpdate({
			suspectUpdate: {
				suspect_link: suspect.suspect_link,
				status: 'ARRESTED',
			},
			pendingMsg: 'Marking suspect as arrested...',
			successMsg: 'Suspect marked as arrested.',
		});
	};

	const updateSuspectScore = (suspect, score) => {
		if (saving)
			return;

		if (!suspect?.suspect_link) {
			setMsgs(['Invalid suspect link.']);
			return;
		}

		submitSuspectUpdate({
			suspectUpdate: {
				suspect_link: suspect.suspect_link,
				score: score,
			},
			pendingMsg: 'Updating suspect score...',
			successMsg: 'Suspect score updated.',
		});
	};

	const openSuspectCriminalRecord = suspect => {
		const suspectId = getSuspectId(suspect);
		if (!suspectId) {
			setMsgs(['Invalid suspect id.']);
			return;
		}
		navigate(`/cases/${cas.id}/suspects/${suspectId}/criminal-record`);
	};

	const openInvestigationApprovalModal = () => {
		if (saving)
			return;

		let modalId = '';
		const closeModal = () => {
			if (modalId) modalApi.close(modalId);
		};

		modalId = modalApi.openNewModal(
			<InvestigationApprovalModal
				caseId={cas.id}
				onClose={closeModal}
				onSubmitted={() => {
					closeModal();
					setMsgs(['Investigation approval submitted successfully.']);
					if (onReload) onReload();
				}}
			/>
		);
	};

	const openEvidenceCreateModal = () => {
		if (saving)
			return;

		let modalId = '';
		const closeModal = () => {
			if (modalId) modalApi.close(modalId);
		};

		modalId = modalApi.openNewModal(
			<EvidenceCreateModal
				caseId={cas.id}
				onClose={closeModal}
				onSubmitted={() => {
					closeModal();
					setMsgs(['Evidence created successfully.']);
					if (onReload) onReload();
				}}
			/>
		);
	};

	const submitGuiltAssesment = () => {
		if (saving)
			return;

		setSaving(true);
		setMsgs(['Submitting guilt assesment...']);
		session.post('/api/submission/', {
			submission_type: 'GUILT_ASSESMENT',
			payload: { case_id: cas.id },
		})
			.then(() => {
				setMsgs(['Guilt assesment submission created successfully.']);
				if (onReload) onReload();
			})
			.catch(err => setMsgs(error_msg_list(err)))
			.finally(() => setSaving(false));
	};

	const openGuiltAssesmentConfirm = () => {
		if (saving)
			return;

		let modalId = '';
		const closeModal = () => {
			if (modalId) modalApi.close(modalId);
		};

		modalId = modalApi.openNewModal(
			<ConfirmDialog
				onConfirm={() => {
					closeModal();
					submitGuiltAssesment();
				}}
				onCancel={closeModal}
			>
				<p>Do you want to start guilt assesment for this case?</p>
			</ConfirmDialog>
		);
	};

	const role = cas.your_role.toLowerCase()

	return (
		<div className=''>
			{/* <div style={{ display: 'flex', gap: '8px' }}>
				{ onReload && <button onClick={onReload}>Reload</button> }
				{ onReturn && <button onClick={onReturn}>Return</button> }
				<button onClick={() => navigate(`/cases/${cas.id}/edit`)}>edit</button>
				<button onClick={() => navigate(`/cases/${cas.id}/detective-board`)}>board</button>
			</div> */}
			<div className='text-left p-0 flex flex-col gap-8'>
				{msgs.map((x, i) => <p key={i}>{x}</p>)}
				<div className='flex flex-row'>
					<div className='grow'>
						<h1 className='p-0 m-0'>{cas.title}</h1>
						<p style={{ whiteSpace: 'pre-wrap' }}>{cas.description}</p>
					</div>
					<div className='flex flex-row flex-nowrap gap-2 items-start'>
							{role==="detective"?
								<button className='btn btn-lg whitespace-nowrap' onClick={()=> navigate(`/cases/${cas.id}/detective-board`)}>
									board
								</button>
							:null}
							{(role==="detective" && cas.status === "open")?
								<button className='btn btn-lg whitespace-nowrap' onClick={openInvestigationApprovalModal}>
									suggest suspects
								</button>
							:null}
							{((role==="detective" || role==="supervisor" || role==="surgent") && cas.status === "interogation")?
								<button className='btn btn-lg whitespace-nowrap' onClick={openGuiltAssesmentConfirm}>
									asses guilts
								</button>
							:null}
						</div>
					</div>
				<div className=''>
					<div className='w-full border-1 p-1'>
						<h2>Details</h2>
					</div>
					<div
						className='mt-2 grid gap-2'
						style={{ gridTemplateColumns: '1fr max-content', minHeight: '12rem' }}
					>
						<div
							className='grid gap-2 h-full'
							style={{ gridTemplateRows: '2fr 1fr' }}
						>
							<div className='border-dotted border-1  p-2'>
								<h2>Status: {normalizeString(cas.status)}</h2>
								<p>{case_status_description[cas.status]}</p>
							</div>
							<div className='border-dotted border-1 flex flex-col justify-center p-2'>
								<h2>Crime Level: {case_crime_level_name[cas.crime_level]}</h2>
							</div>
						</div>
						<div
							className='grid gap-2 h-full'
							style={{ gridTemplateRows: '1fr 2fr' }}
						>
							<div className='border-dotted border-1 flex flex-col justify-center p-2'>
								<h2>Role: {cas.your_role.toLowerCase()}</h2>
							</div>
							<div className='border-dotted border-1 flex flex-col justify-center p-2'>
								<h2>Lead Detective: {cas.lead_detective}</h2>
								<h2>Supervisor: {cas.supervisor}</h2>
							</div>
						</div>
					</div>
				</div>
				{/* <div className='border-dotted border-1 p-2 flex flex-col gap-4'> */}
					<TitledBox title={"Suspects"} className='min-h-40'>
						{(cas.suspects || []).length === 0 ? (
							<h2>No suspects yet</h2>
						) : (
							(cas.suspects || []).map((sus) => (
								<SuspectCard
									your_role={cas.your_role}
									key={sus.id || sus.national_id}
									user={sus}
									onScoreUpdate={updateSuspectScore}
									onMarkArrested={markSuspectArrested}
									onViewCriminalRecord={openSuspectCriminalRecord}
									cas={cas}
								/>
							))
						)}
					</TitledBox>
					<TitledBox title={"Complainants"} className=' flex flex-row flex-wrap gap-2'>
							{
								complainants.map((com)=>{
									return (
										<UserCard key={com.id || com.national_id} user={com} onDelete={removeComplainant}/>
									)
								})
							}
							<div className='user-card'>
								<div className='grow'>
									Add a complainant
								</div>
								<div className='flex flex-row gap-1'>
									<input
										className='input grow'
										placeholder='national id'
										value={newComplainantNid}
										onChange={e => setNewComplainantNid(e.target.value)}
									/>
									<button className='btn float-right' onClick={addComplainant} disabled={saving}>
										Add
									</button>
								</div>
							</div>
					</TitledBox>
					<TitledBox title={"Witnesses"} className='flex flex-row flex-wrap gap-2'>
							{
								witnesses.map((com)=>{
									return(<UserCard key={com.id || com.national_id} user={com} onDelete={removeWitness}/>)
								})
							}
							<div className='user-card'>
								<div className='grow'>
									Add a witness
								</div>
								<div className='flex flex-row gap-1'>
									<input
										className='input grow'
										placeholder='national id'
										value={newWitnessNid}
										onChange={e => setNewWitnessNid(e.target.value)}
									/>
									<button className='btn float-right' onClick={addWitness} disabled={saving}>
										Add
									</button>
								</div>
							</div>
					</TitledBox>
					<TitledBox title={"evidence"} className='min-h-40'>
						<>
							<Retrieve msg="evidence" path={`/api/cases/${cas.id}/evidences/`} then={
								(res, onReload) => (<EvidenceList list={res.map(evi_decode)}/>)
							}/>
							<div className='w-full text-right'>
								<button className="btn btn-lg" onClick={openEvidenceCreateModal}>
									create
								</button>
							</div>
						</>
					</TitledBox>
				{/* </div> */}

			</div>
		</div>
	);
}

export function CaseFrame({ cas, safeOnly, ...props }) {
	const compact = useContext(ListCompactCtx);
	const hiddenFields = ['title', 'description', 'status', 'crime_datetime'];
	const fields = (safeOnly
		? case_fields.filter(([,, id]) => case_safe_fields.includes(id))
		: case_fields
	).filter(([,, id]) => !hiddenFields.includes(id));
	const navigate = useNavigate();
	
	const Process = (type, name, id) => FormField(type, name, cas[id], { key: id, compact });
	const ProcessArr = ent => Process(...ent);

	console.log(cas)

	return (
		<>
			<div className='generic-list-item case-list-item' {...props} onClick={() => navigate(`/cases/${cas.id}`)}>
				<div className='flex flex-col gap-0'>
					<div className='flex flex-row'>
						<h2 className='text-left grow'>
							{cas.title}
						</h2>
						<h3>
							{normalizeString(cas.status, NormalizationType.LOWER_CASE)}
						</h3>
					</div>
					<h3>
						{cas.description}
					</h3>
					<div className='text-(--c-text-muted)'>
						crime date: {formatDate(cas.crime_datetime)}
					</div>
				</div>
				<div className='grow'>
					{fields.map(ProcessArr)}
				</div>
			</div>
		</>
	);
}

export const CaseList = ({ list, title, onReload, onReturn, safeOnly }) => (
	<GenericList title={title} onReload={onReload} onReturn={onReturn}>
		{list.map((cas, i) => (<CaseFrame key={i} cas={cas} safeOnly={safeOnly}/>))}
	</GenericList>
);

export default CaseList
