import { useState, useEffect, useContext } from 'react'
import { useNavigate, useLocation, Link } from 'react-router'
import { FormInputField, FormInputChangeFn, FormField, GenericList, ListCompactCtx, form_list_decode } from './Forms'
import { session, error_msg, error_msg_list } from './session'
import { useModal } from './modals/ModalHost';
import { formatDate, NormalizationType, normalizeString } from './utils';
import { Retrieve } from './App';
import { CustomSelect } from './CustomSelect';
import { EvidenceFrame, evi_decode } from './Evidence';
// type, name, id
const subm_fields_common = [
	['text', 'Title (optional)', 'title'],
	['textarea', 'Description', 'description'],
	['datetime', 'Crime Datetime', 'crime_datetime'],
];
const subm_fields = {
	CRIME_SCENE: [
		...subm_fields_common,
		['list !First_Name !Last_Name !Phone .National_ID', 'Witnesses', 'witnesses'],
	],
	COMPLAINT: [
		...subm_fields_common,
		['list !First_Name !Last_Name !Phone .National_ID', 'Complainants', 'complainants'],
	],
	BIO_EVIDENCE: [],
	DATA_REWARD: [
		['textarea', 'Details', 'description'],
	],
	BAIL_REQUEST: [],
	CASE_STAFFING: [
		['text', 'Level', 'crime_level'],
		['text', 'Lead Detective', 'lead_detective'],
		['text', 'Supervisor', 'supervisor'],
		['text', 'Case Title', 'title'],
	],
	INVESTIGATION_APPROVAL: [
		['text', 'Case ID', 'case'],
		['list !First_Name !Last_Name !Phone .National_ID', 'Suggested Suspects', 'suggested_suspects'],
	],
	GUILT_ASSESMENT: [
		['text', 'Case ID', 'case_id'],
	],
};

const subm_secondary_actions = {
	GUILT_ASSESMENT: ["VIEW_CASE_DETAILS"],
	BIO_EVIDENCE: ["VIEW_EVIDENCE"],
}
const subm_types = [...Object.keys(subm_fields)];
const submissionStatusClassMap = Object.freeze({
	APPROVED: 'text-[var(--c-primary)] border-[var(--c-primary)] bg-[var(--c-primary)]/10',
	ACCEPTED: 'text-[var(--c-primary)] border-[var(--c-primary)] bg-[var(--c-primary)]/10',
	REJECTED: 'text-[var(--c-danger)] border-[var(--c-danger)] bg-[var(--c-danger)]/10',
	PENDING: 'text-[var(--c-warning)] border-[var(--c-warning)] bg-[var(--c-warning)]/10',
});

function getSubmissionStatusClass(status) {
	const key = String(status ?? '').trim().toUpperCase();
	return submissionStatusClassMap[key] ?? 'text-[var(--c-text-muted)] border-[var(--c-border)] bg-[var(--c-surface-2)]';
}

export function SubmissionSubmitForm({ subm0, resubmit, typeList, returnTo, onSubmitted, submissionType, fixedFields }) {
	const types = typeList && typeList.length? typeList: subm_types.map(x => { return { key: x, value: x }});
	const fixedType = submissionType && subm_fields[submissionType] ? submissionType : null;
	const fixedFieldValues = fixedFields && typeof fixedFields === 'object' ? fixedFields : {};
	const isFixedField = id => Object.prototype.hasOwnProperty.call(fixedFieldValues, id);

	const defaultData = () => {
		let obj = {submission_type: fixedType || types[0].key};

		for (const t of subm_types)
			for (const ent of subm_fields[t])
				obj[ent[2]] = '';

		if (subm0) {
			obj = { ...obj, ...form_list_decode(subm0, {
				witnesses: ['national_id'],
				complainants: ['national_id'],
				suggested_suspects: ['national_id'],
			})}
		}

		obj = { ...obj, ...fixedFieldValues };

		return obj;
	};
	const [data, setData] = useState(defaultData);
	const [post, setPost] = useState(false);
	const [msgs, setMsgs] = useState([]);
	const navigate = useNavigate();
	const setMsg = msg => setMsgs([msg]);
	const fields = subm_fields[data.submission_type];

	useEffect(() => {
		if (!fixedType && !Object.keys(fixedFieldValues).length) return;
		setData(prev => ({
			...prev,
			...(fixedType ? { submission_type: fixedType } : {}),
			...fixedFieldValues,
		}));
	}, [fixedType, fixedFieldValues]);

	const submit = () => {
		const payload = {};
		for (const [,, id] of fields)
			payload[id] = data[id];
		for (const [id, val] of Object.entries(fixedFieldValues))
			payload[id] = val;

		for (const [id1, id2] of [
				['witnesses', 'witnesses_national_ids'],
				['complainants', 'complainant_national_ids'],
				['suggested_suspects', 'suggested_suspects_national_ids'],
		]) {
			if (payload[id1]) {
				payload[id2] = payload[id1].map(([x]) => x);
				delete payload[id1];
			}
		}

		for (const id in payload)
			if (payload[id] === '' && !isFixedField(id))
				delete payload[id];

		if (typeof payload.title === 'string' && payload.title.trim() === '')
			delete payload.title;

		const req = resubmit !== undefined ? { action_type: 'RESUBMIT', payload }: { submission_type: data.submission_type, payload };

		setPost(true);
		setMsg('Awaiting response...');

		const path = resubmit !== undefined? `/api/submission/${resubmit}/actions/`: '/api/submission/';
		session.post(path, req)
			.then(res => {
				setMsg('Submit successful');
				setData(defaultData());
				if (onSubmitted) onSubmitted(res);
				if (returnTo) navigate(returnTo);
			})
			.catch(err => setMsgs(error_msg_list(err)))
			.finally(() => setPost(false));
	}

	const ChangeFn = (type, id) => FormInputChangeFn(data, setData, type, id);
	const Field = (type, name, id) => FormInputField(type, name, data[id], ChangeFn(type, id), { id: id });
	const FieldArr = arr => Field(arr[0], arr[1], arr[2]);

	return (<>
		{/* <h1>{resubmit === undefined? 'New Submission': 'Edit Submission'}</h1> */}
		<div className='absolute translate-y-full -bottom-2 bg-black'>
			{msgs.map((x, i) => <p key={i} style={{ textAlign: 'center' }}>{x}</p>)}
		</div>
		<div className='flex flex-col gap-7'>
			{resubmit === undefined && !fixedType ? (
				<div className='submission-type-panel'>
					{/* <select
						id='submission_type'
						value={data.submission_type}
						onChange={ChangeFn('text', 'submission_type')}
						className='input submission-type-select w-full'
					>
						{types.map(({ key, name, value }) => (
							<option key={key} value={key}>{name ?? value ?? key}</option>
						))}
					</select> */}
						<CustomSelect
							id="submission_type"
							name="submission_type"
							value={data.submission_type}
							onChange={ChangeFn("text", "submission_type")}
							options={types}
							className="w-full"
							buttonClassName="custom-select-button"
							menuClassName="custom-select-menu"
							optionClassName="custom-select-option"
						/>
				</div>
			) : null}
			<div className='flex flex-col gap-2'>
				{fields.filter(([, , id]) => !isFixedField(id)).map(ent => FieldArr(ent))}
			</div>
			<button className='btn w-full' onClick={submit} disabled={post}>Submit</button>
		</div>
			{/* {subm_fields_common.map(ent => FieldArr(ent))} */}
	</>)
}

export function SubmissionFrame({ subm, onAction, ...props }) {
	const meta_fields = [
		['text', 'Type', 'submission_type'],
		['text', 'Status', 'status'],
		['datetime', 'Created at', 'created_at'],
	];
	const compact = useContext(ListCompactCtx);
	const type = subm.submission_type;
	const type_normalized = normalizeString(type)
	const secondary_actions = subm_secondary_actions[type]??[]
	const actions = [...secondary_actions, ...subm.available_actions];
	const last_action = subm.actions_history[0] ? subm.actions_history[0]: [];
	const createdAtFormatted = formatDate(subm.created_at);
	const statusClassName = getSubmissionStatusClass(subm.status);
	
	
	const Process = data => (type, name, id) => FormField(type, name, data[id], { key: id, compact });
	const ProcessArr = data => (ent) => Process(data)(...ent);
	return (
		<div className='generic-list-item' {...props}>
			<div className='flex flex-col gap-0'>
				<div className='flex flex-row'>
					<h2 className='text-left grow'>
						{type_normalized}
					</h2>
					<div className={`border-1 px-2 py-0.5 text-sm whitespace-nowrap ${statusClassName}`}>
						{normalizeString(subm.status, NormalizationType.LOWER_CASE)}
					</div>
				</div>
				<div>
					<p title={subm.created_at ?? ''} className='text-gray-400'>
						date
						{createdAtFormatted}
					</p>
				</div>
			</div>
			<div className='grow'>
				{subm_fields[type].map(ProcessArr(subm.target))}
				{type === 'DATA_REWARD'
					? (
						<>
							{FormField('text', 'Related Case', subm.target?.data_reward_case_id ?? '-', { key: 'data_reward_case_id', compact })}
							{FormField('text', 'Reward Amount', subm.target?.data_reward_reward_amount_display ?? '-', { key: 'data_reward_reward_amount_display', compact })}
						</>
					)
					: null}
				{last_action && last_action.action_type === 'REJECT' && FormField('text', 'Last Message', last_action.payload.message, {})}
			</div>
			<div className='w-full flex flex-row gap-2 justify-end'>
				{actions.map((act, idx) => (<button className='btn btn-sm' key={idx} onClick={() => onAction(act)}>{normalizeString(act)}</button>))}
			</div>
		</div>
		);
	}

export const subm_decode = subm => {
	const actionsHistory = Array.isArray(subm?.actions_history) ? subm.actions_history : [];
	const findPayloadValue = key => {
		for (const action of actionsHistory) {
			const payload = action?.payload;
			if (payload && payload[key] !== undefined && payload[key] !== null && payload[key] !== '')
				return payload[key];
		}
		return null;
	};
	const rewardAmountValue = findPayloadValue('reward_amount')
		?? subm?.target?.reward_amount
		?? subm?.target?.reward?.amount
		?? null;

	return { ...subm, target: {
		...form_list_decode(subm.target, {
			witnesses         : ['first_name', 'last_name', 'phone_number'],
			complainants      : ['first_name', 'last_name', 'phone_number'],
			suggested_suspects: ['first_name', 'last_name', 'phone_number'],
		}),
		case: subm.target.case_details?.id,
		case_id: subm.target.case_id ?? subm.target.id,
		data_reward_case_id: findPayloadValue('case_id') ?? '-',
		data_reward_reward_amount: rewardAmountValue,
		data_reward_reward_amount_display: rewardAmountValue === null ? '-' : String(rewardAmountValue),
		//case_details: subm.target.case_details && case_decode(subm.target.case_details),
	}};
}

function RejectSubmissionModal({ onCancel, onReject }) {
	const [message, setMessage] = useState('');

	return (
		<div style={{ width: 'min(32rem, 100%)' }}>
			<div className='flex flex-col gap-2'>
				<h2 className='m-0'>Reject Submission</h2>
				<p className='m-0'>Provide a rejection message:</p>
				<textarea
					value={message}
					onChange={e => setMessage(e.target.value)}
					rows={5}
					placeholder='Write rejection message...'
					className='w-full'
				/>
				<div className='flex justify-end flex-row gap-2'>
					<button className='btn btn-red' onClick={onCancel}>Cancel</button>
					<button
						className='btn btn-green'
						disabled={!message.trim()}
						onClick={() => onReject(message.trim())}
					>
						Reject
					</button>
				</div>
			</div>
		</div>
	);
}

function AssessGuiltsModal({ suspects, onCancel, onSubmit }) {
	const [selected, setSelected] = useState([]);
	const suspectEntries = (suspects || [])
		.map(sus => {
			const suspectLinkId = sus?.suspect_link;
			if (suspectLinkId === null || suspectLinkId === undefined)
				return null;
			const suspectName = [sus.first_name, sus.last_name].filter(Boolean).join(' ') || sus.national_id || `#${suspectLinkId}`;
			return { suspectLinkId, suspectName };
		})
		.filter(Boolean);

	const toggle = suspectLinkId => {
		setSelected(prev =>
			prev.includes(suspectLinkId)
				? prev.filter(id => id !== suspectLinkId)
				: [...prev, suspectLinkId]
		);
	};

	return (
		<div className='flex flex-col gap-2 h-50'>
			<div>
				<h2 className='m-0'>Assess Guilts</h2>
				<p className='m-0'>Select guilty suspects:</p>
			</div>
			<div className='flex flex-col gap-2 grow'>
				{
					suspectEntries.map(({ suspectLinkId, suspectName }) => {
						const isSelected = selected.includes(suspectLinkId);
						return (
							<>
								<button
									key={suspectLinkId}
									className={'btn w-full text-left ' + (isSelected ? 'bg-gray-300' : '')}
									onClick={() => toggle(suspectLinkId)}
								>
									{suspectName}
								</button>
							</>
						);
					})
				}
			</div>
			<div className='flex justify-end flex-row gap-2'>
				<button className='btn btn-red' onClick={onCancel}>Cancel</button>
				<button
					className='btn btn-green'
					disabled={selected.length === 0}
					onClick={() => onSubmit(selected)}
				>
					Submit
				</button>
			</div>
		</div>
	);
}

function AcceptBailRequestModal({ onCancel, onSubmit }) {
	const [amount, setAmount] = useState('');
	const parsedAmount = Number(amount);
	const validAmount = Number.isInteger(parsedAmount) && parsedAmount > 0;

	return (
		<div className='flex flex-col gap-3'>
			<div>
				<h2 className='m-0'>Accept Bail Request</h2>
				<p className='m-0'>Specify the amount the user should pay:</p>
			</div>
			<input
				type='number'
				min='1'
				step='1'
				placeholder='Amount'
				className='input'
				value={amount}
				onChange={e => setAmount(e.target.value)}
			/>
			<div className='flex justify-end flex-row gap-2'>
				<button className='btn btn-red' onClick={onCancel}>Cancel</button>
				<button
					className='btn btn-green'
					disabled={!validAmount}
					onClick={() => onSubmit(parsedAmount)}
				>
					Submit
				</button>
			</div>
		</div>
	);
}

function DataRewardCaseSelectModal({ onCancel, onSubmit }) {
	const [caseId, setCaseId] = useState('');
	const parsedCaseId = Number(caseId);
	const validCaseId = Number.isInteger(parsedCaseId) && parsedCaseId > 0;

	return (
		<div className='flex flex-col gap-3'>
			<div>
				<h2 className='m-0'>Approve Data Reward</h2>
				<p className='m-0'>Enter the related case ID for this report:</p>
			</div>
			<input
				type='number'
				min='1'
				step='1'
				placeholder='Case ID'
				className='input'
				value={caseId}
				onChange={e => setCaseId(e.target.value)}
			/>
			<div className='flex justify-end flex-row gap-2'>
				<button className='btn btn-red' onClick={onCancel}>Cancel</button>
				<button
					className='btn btn-green'
					disabled={!validCaseId}
					onClick={() => onSubmit(parsedCaseId)}
				>
					Submit
				</button>
			</div>
		</div>
	);
}

function DataRewardAmountModal({ onCancel, onSubmit }) {
	const [amount, setAmount] = useState('');
	const parsedAmount = Number(amount);
	const validAmount = Number.isInteger(parsedAmount) && parsedAmount > 0;

	return (
		<div className='flex flex-col gap-3'>
			<div>
				<h2 className='m-0'>Set Reward Amount</h2>
				<p className='m-0'>Enter how much reward this user should receive:</p>
			</div>
			<input
				type='number'
				min='1'
				step='1'
				placeholder='Reward Amount'
				className='input'
				value={amount}
				onChange={e => setAmount(e.target.value)}
			/>
			<div className='flex justify-end flex-row gap-2'>
				<button className='btn btn-red' onClick={onCancel}>Cancel</button>
				<button
					className='btn btn-green'
					disabled={!validAmount}
					onClick={() => onSubmit(parsedAmount)}
				>
					Submit
				</button>
			</div>
		</div>
	);
}

function BioEvidenceModal({ evidence, onClose }) {
	const baseEvidence = evidence || {};
	const decodedEvidence = evi_decode({
		...baseEvidence,
		resource_type: baseEvidence.resource_type || 'BioEvidence',
	});
	const evidenceForFrame = {
		...decodedEvidence,
		type: decodedEvidence.type || 'bio',
	};

	return (
		<div style={{ width: 'min(56rem, 100%)' }}>
			<div className='flex flex-row items-center justify-between mb-2'>
				<h2 className='m-0'>Bio Evidence</h2>
				<button className='btn' onClick={onClose}>close</button>
			</div>
			<div className='h-[70vh] max-h-[70vh] min-h-120'>
				<EvidenceFrame
					evi={evidenceForFrame}
					className='border-1 border-(--c-border) bg-(--c-surface) flex flex-col gap-2 h-full p-2 overflow-hidden'
				/>
			</div>
		</div>
	);
}

export function SubmissionList({ list, title, onReload, onReturn, create_button=false, description=null }) {
	const [phase, setPhase] = useState(2);
	const [str, setStr] = useState('');
	const navigate = useNavigate();
	const location = useLocation();
	const modalApi = useModal();

	const submitAction = (id, act, payload = {}) => {
		setPhase(3);
		setStr('Awaiting response...');
		session.post(`/api/submission/${id}/actions/`, { action_type: act, payload })
			.then(onReload)
			.catch(e => { setStr(error_msg(e)); setPhase(2); });
	};

	const openRejectModal = id => {
		modalApi.openNewModal(
			<RejectSubmissionModal
				onCancel={modalApi.closeTop}
				onReject={message => {
					modalApi.closeTop();
					submitAction(id, 'REJECT', { message });
				}}
			/>
		);
	};

	const openAssessGuiltsModal = async subm => {
		const id = subm.id;
		const suspects = subm?.target?.suspects;

		modalApi.openNewModal(
			<AssessGuiltsModal
				suspects={suspects}
				onCancel={modalApi.closeTop}
				onSubmit={selectedSuspectLinkIds => {
					submitAction(id, 'ASSESS_GUILTS', { guilty_suspects_ids: selectedSuspectLinkIds });
					modalApi.closeTop();
				}}
			/>
		);
	};

	const openBailAmountModal = id => {
		modalApi.openNewModal(
			<AcceptBailRequestModal
				onCancel={modalApi.closeTop}
				onSubmit={amount => {
					submitAction(id, 'ACCEPT', { amount });
					modalApi.closeTop();
				}}
			/>
		);
	};

	const openDataRewardCaseSelectModal = id => {
		modalApi.openNewModal(
			<DataRewardCaseSelectModal
				onCancel={modalApi.closeTop}
				onSubmit={caseId => {
					submitAction(id, 'ACCEPT', { case_id: caseId });
					modalApi.closeTop();
				}}
			/>
		);
	};

	const openDataRewardAmountModal = id => {
		modalApi.openNewModal(
			<DataRewardAmountModal
				onCancel={modalApi.closeTop}
				onSubmit={rewardAmount => {
					submitAction(id, 'ACCEPT', { reward_amount: rewardAmount });
					modalApi.closeTop();
				}}
			/>
		);
	};

	const openBioEvidenceModal = subm => {
		modalApi.openNewModal(
			<BioEvidenceModal
				evidence={subm?.target}
				onClose={modalApi.closeTop}
			/>
		);
	};

	const openSubmissionCreateModal = () => {
		modalApi.openNewModal(
			<Retrieve msg="submission types" path='/api/submission/types/'
				then={({ types }) => (<SubmissionSubmitForm typeList={types} onSubmitted={modalApi.closeTop} />)}
			/>
		);
	}

	const getSubmissionCaseId = subm =>
		subm?.target?.case_id
		?? subm?.target?.case
		?? subm?.case_id
		?? subm?.case?.id
		?? null;

	const onAction = subm => act => {
		const id = subm.id;
		const caseId = getSubmissionCaseId(subm);

		if (phase !== 2)
			return;
		window.scrollTo(0, 0);
		if (act === 'ACCEPT' && subm.submission_type === 'BAIL_REQUEST') {
			openBailAmountModal(id);
		} else if (act === 'ACCEPT' && subm.submission_type === 'DATA_REWARD') {
			const hasCaseLinked = (subm?.actions_history || []).some(action =>
				action?.action_type === 'ACCEPT'
				&& action?.payload
				&& action.payload.case_id !== undefined
				&& action.payload.case_id !== null
			);
			if (hasCaseLinked)
				openDataRewardAmountModal(id);
			else
				openDataRewardCaseSelectModal(id);
		} else if (act === 'ACCEPT' || act === 'APPROVE') {
			submitAction(id, act);
		} else if (act === 'REJECT') {
			openRejectModal(id);
			} else if (act === 'RESUBMIT') {
				const params = new URLSearchParams({ redir: location.pathname }).toString();
				navigate(`/submission/${id}/edit?${params}`);
			} else if (act === 'ASSESS_GUILTS') {
				openAssessGuiltsModal(subm);
			} else if (act === 'VIEW_CASE_DETAILS') {
			if (!caseId) {
				setStr('This submission is not linked to a case.');
				return;
			}
			navigate(`/cases/${caseId}/`);
		} else if (act === 'VIEW_EVIDENCE') {
			if (subm.submission_type !== 'BIO_EVIDENCE') {
				setStr('This submission is not linked to an evidence item.');
				return;
			}
			openBioEvidenceModal(subm);
		} else {
			alert('Unimplemented: ' + act);
		}
	};
	return (
		<div className='relative w-full h-full'>
				<GenericList title={title} onReload={onReload} onReturn={onReturn} msg={str} description={description}>
					{list.map((subm, i) => (<SubmissionFrame key={i} subm={subm} onAction={onAction(subm)}/>))}
				</GenericList>
			{create_button?<button onClick={openSubmissionCreateModal} className='absolute right-2 bottom-2 btn btn-lg'>create</button>:null}
		</div>
	)
}

export default SubmissionSubmitForm
