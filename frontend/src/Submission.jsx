import { useState, useEffect, useContext } from 'react'
import { useNavigate, useLocation, Link } from 'react-router'
import { FormInputField, FormInputChangeFn, FormField, SimpleField, GenericList, ListCompactCtx, form_list_decode } from './Forms'
import { session, error_msg, error_msg_list } from './session'

// type, name, id
const subm_fields_common = [
	['text', 'Title', 'title'],
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
	CASE_STAFFING: [
		['text', 'Level', 'crime_level'],
		['text', 'Lead Detective', 'lead_detective'],
		['text', 'Supervisor', 'supervisor'],
		['text', 'Origin PK', 'origin_submission_id'],
	],
	INVESTIGATION_APPROVAL: [
		['text', 'Case ID', 'case'],
		['list !First_Name !Last_Name !Phone .National_ID', 'Suggested Suspects', 'suggested_suspects'],
	],
};
const subm_types = [...Object.keys(subm_fields)];


export function SubmissionSubmitForm({ subm0, resubmit, returnTo }) {
	const isResubmit = resubmit !== undefined;

	const inferType = () => {
		if (!subm0)
			return subm_types[0];
		if (subm0.submission_type && subm_types.includes(subm0.submission_type))
			return subm0.submission_type;

		for (const t of subm_types)
			if (subm_fields[t].some(([, , id]) => subm0[id] !== undefined))
				return t;

		return subm_types[0];
	};
	const [submissionType, setSubmissionType] = useState(inferType);
	const [typeOptions, setTypeOptions] = useState(() => subm_types.map(key => ({ key, name: key })));
	const [typeListLoaded, setTypeListLoaded] = useState(isResubmit);

	const defaultData = () => {
		const obj = {}
		// for (const ent of subm_fields_common)
		// 	obj[ent[2]] = '';
		for (const t of subm_types)
			for (const ent of subm_fields[t])
				obj[ent[2]] = '';

		if (!subm0)
			return obj;

		const parsed = { ...obj, ...subm0 };
		if (subm0.witnesses)
			parsed.witnesses = subm0.witnesses.map(x => [x.national_id]);
		if (subm0.complainants)
			parsed.complainants = subm0.complainants.map(x => [x.national_id]);
		return parsed;
	};
	const [data, setData] = useState(defaultData);
	const [post, setPost] = useState(false);
	const [msgs, setMsgs] = useState([]);
	const navigate = useNavigate();
	const setMsg = msg => setMsgs([msg]);
	const currentTypeFields = subm_fields[submissionType] || [];

	useEffect(() => {
		if (isResubmit)
			return;

		setTypeListLoaded(false);
		session.get('/api/submission/types/')
		.then(res => {
				const fromApi = Array.isArray(res.data?.types)? res.data.types: [];
				const supported = fromApi.filter(ent => subm_fields[ent.key] !== undefined);
				setTypeOptions(supported);
				if (supported.length > 0)
					setSubmissionType(cur => supported.some(ent => ent.key === cur)? cur: supported[0].key);
				else
					setMsgs(['No supported submission type is available for this account.']);
			})
			.catch(err => setMsgs(error_msg_list(err)))
			.finally(() => setTypeListLoaded(true));
	}, [isResubmit]);

	const submit = () => {
		const payload = {};
		for (const [, , id] of currentTypeFields) {
			payload[id] = data[id];
		}
		if (payload.witnesses) {
			payload.witnesses_national_ids = payload.witnesses.map(([x]) => x);
			delete payload.witnesses;
		}
		if (payload.complainants) {
			payload.complainant_national_ids = payload.complainants.map(([x]) => x);
			delete payload.complainants;
		}
		if (payload.suggested_suspects) {
			payload.suggested_suspects_national_ids = payload.suggested_suspects.map(([x]) => x);
			delete payload.suggested_suspects;
		}
		for (const id in payload)
			if (payload[id] === '')
				delete payload[id];
		const req = resubmit !== undefined ? { action_type: 'RESUBMIT', payload }: { submission_type: submissionType, payload };

		setPost(true);
		setMsg('Awaiting response...');

		const path = resubmit !== undefined? `/api/submission/${resubmit}/actions/`: '/api/submission/';
		session.post(path, req)
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
	const FieldArr = arr => Field(arr[0], arr[1], arr[2]);

	return (<>
		{ submissionType === 'COMPLAINT' && <h1>Complaint Submission</h1> }
		{ submissionType === 'CRIME_SCENE' && <h1>Crime Scene Report</h1> }
		{msgs.map((x, i) => <p key={i} style={{ textAlign: 'center' }}>{x}</p>)}
		<div style={{ maxWidth: '500px', margin: '0 auto' }}>
			{!isResubmit && SimpleField('Type', (
				<select
					id='submission_type'
					value={submissionType}
					onChange={e => setSubmissionType(e.target.value)}
					disabled={!typeListLoaded}
					style={{ width: '100%' }}
				>
					{typeOptions.map(ent => (<option key={ent.key} value={ent.key}>{ent.name}</option>))}
				</select>
			), { id: 'submission_type' })}
			{/* {subm_fields_common.map(ent => FieldArr(ent))} */}
			{currentTypeFields.map(ent => FieldArr(ent))}
			<button onClick={submit} disabled={post || !typeListLoaded || currentTypeFields.length === 0} style={{ width: '100%' }}>Submit</button>
		</div>
	</>)
}

export function SubmissionFrame({ subm, onAction, ...props }) {
	const meta_fields = [
		['text', 'Type', 'submission_type'],
		['text', 'Status', 'status'],
		['datetime', 'Created at', 'created_at'],
	];
	const compact = useContext(ListCompactCtx);
	const [rejMsg, setRejMsg] = useState('');
	const type = subm.submission_type;
	const actions = subm.available_actions;
	const last_action = subm.actions_history[0] ? subm.actions_history[0]: [];
	
	
	const Process = data => (type, name, id) => FormField(type, name, data[id], { key: id, compact });
	const ProcessArr = data => (ent) => Process(data)(...ent);
	return (
		<div className='item' {...props}>
			{meta_fields.map(ProcessArr(subm))}
			{/* {subm_fields_common.map(ProcessArr(subm.target))} */}
			{subm_fields[type].map(ProcessArr(subm.target))}
			{last_action && last_action.action_type === 'REJECT' && FormField('text', 'Last Message', last_action.payload.message, {})}
			{actions.includes('REJECT') && FormInputField('textarea', 'Rejection Message', rejMsg, e => setRejMsg(e.target.value), {})}
			{actions.map((act, idx) => (<button key={idx} onClick={() => onAction(act, rejMsg)}>{act}</button>))}
		</div>
	);
}

export const subm_decode = subm => {
	return { ...subm, target: {
		...form_list_decode(subm.target, {
			witnesses         : ['first_name', 'last_name', 'phone_number'],
			complainants      : ['first_name', 'last_name', 'phone_number'],
			suggested_suspects: ['first_name', 'last_name', 'phone_number'],
		}),
		case: subm.target.case_details?.id,
		//case_details: subm.target.case_details && case_decode(subm.target.case_details),
	}};
}

export function SubmissionList({ list, title, onReload, onReturn, create_button=false, description=null }) {
	const [phase, setPhase] = useState(2);
	const [str, setStr] = useState('');
	const navigate = useNavigate();
	const location = useLocation();

	const onAction = id => (act, msg) => {
		if (phase !== 2)
			return;
		window.scrollTo(0, 0);
		if (act === 'ACCEPT' || act === 'APPROVE' || act === 'REJECT') {
			const payload = {};
			if (act === 'REJECT') payload.message = msg;

			setPhase(3);
			setStr('Awaiting response...')
			session.post(`/api/submission/${id}/actions/`, { action_type: act, payload })
				.then(onReload)
				.catch(e => { setStr(error_msg(e)); setPhase(2); });
		} else if (act === 'RESUBMIT') {
			const params = new URLSearchParams({ redir: location.pathname }).toString();
			navigate(`/submission/${id}/edit?${params}`);
		} else {
			alert('Unimplemented: ' + act);
		}
	};
	return (
		<div className='relative w-full h-full'>
			<GenericList title={title} onReload={onReload} onReturn={onReturn} msg={str} description={description}>
				{list.map((subm, i) => (<SubmissionFrame key={i} subm={subm} onAction={onAction(subm.id)}/>))}
			</GenericList>
			{create_button?<Link to='/submission/new' className='absolute right-2 bottom-2'>create</Link>:null}
		</div>
	)
}

export default SubmissionSubmitForm
