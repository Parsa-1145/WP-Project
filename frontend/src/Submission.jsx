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
	BIO_EVIDENCE: [],
	BAIL_REQUEST: [],
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


export function SubmissionSubmitForm({ subm0, resubmit, typeList, returnTo }) {
	const types = typeList && typeList.length? typeList: subm_types.map(x => { return { key: x, value: x }});

	const defaultData = () => {
		let obj = {submission_type: types[0].key};

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

		return obj;
	};
	const [data, setData] = useState(defaultData);
	const [post, setPost] = useState(false);
	const [msgs, setMsgs] = useState([]);
	const navigate = useNavigate();
	const setMsg = msg => setMsgs([msg]);
	const fields = subm_fields[data.submission_type];

	const submit = () => {
		const payload = {};
		for (const [,, id] of fields)
			payload[id] = data[id];

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
			if (payload[id] === '')
				delete payload[id];

		const req = resubmit !== undefined ? { action_type: 'RESUBMIT', payload }: { submission_type: data.submission_type, payload };

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
		<h1>{resubmit === undefined? 'New Submission': 'Edit Submission'}</h1>
		{msgs.map((x, i) => <p key={i} style={{ textAlign: 'center' }}>{x}</p>)}
		<div style={{ maxWidth: '500px', margin: '0 auto' }}>
			{resubmit === undefined && SimpleField('Type', (
				<select
					id='submission_type'
					value={data.submission_type}
					onChange={ChangeFn('text', 'submission_type')}
				>
					{types.map(({ key, name }) => (<option key={key} value={key}>{name}</option>))}
				</select>
			), { id: 'submission_type' })}
			{/* {subm_fields_common.map(ent => FieldArr(ent))} */}
			{fields.map(ent => FieldArr(ent))}
			<button onClick={submit} disabled={post} style={{ width: '100%' }}>Submit</button>
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
