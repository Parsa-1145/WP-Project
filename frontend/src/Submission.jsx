import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router'
import { FormInputField, FormInputChangeFn, FormField, SimpleField, ResponsiveGrid } from './Forms'
import session from './session'

// type, name, id
const subm_fields_common = [
	['text', 'Title', 'title'],
	['textarea', 'Description', 'description'],
	['datetime', 'Crime Datetime', 'crime_datetime'],
];
const subm_fields = {
	CRIME_SCENE: [
		['list Phone ID', 'Witnesses', 'witnesses'],
	],
	COMPLAINT: [
		['list ID', 'Complainants', 'complainant_national_ids'],
	]
};
const subm_types = [...Object.keys(subm_fields)];

function SubmissionSubmitForm({ type, returnTo }) {
	const defaultData = () => {
		const obj = {}
		for (const ent of subm_fields_common)
			obj[ent[2]] = '';
		for (const ent of subm_fields[type])
			obj[ent[2]] = '';
		return obj;
	};
	const [data, setData] = useState(defaultData);
	const [post, setPost] = useState(false);
	const [msgs, setMsgs] = useState([]);
	const navigate = useNavigate();
	const setMsg = msg => setMsgs([msg]);

	const submit = () => {
		const payload = {...data};
		if (payload.witnesses)
			payload.witnesses = payload.witnesses.map(ent => ({ phone_number: ent[0], national_id: ent[1] }))
		if (payload.complainant_national_ids)
			payload.complainant_national_ids = payload.complainant_national_ids.map(([x]) => x);
		for (const id in payload)
			if (payload[id] === '')
				payload[id] = undefined;
		const req = { submission_type: type, payload };

		setPost(true);
		setMsg('Awaiting response...');

		const obj_dfs = (list, pre, o) => {
			if (Array.isArray(o))
				o.forEach(v => obj_dfs(list, pre, v));
			else if (typeof o === 'object')
				Object.entries(o).forEach(([str, v]) => obj_dfs(list, pre + str + ' - ', v))
			else
				list.push(pre + o);
		}

		session.post('/api/submission/', req)
			.then(res => {
				setMsg('Submit successful');
				setData(defaultData());
				if (returnTo) navigate(returnTo);
			})
			.catch(err => {
				if (err.response) {
					const list = [];
					obj_dfs(list, 'ERR: ', err.response.data);
					setMsgs(list);
				} else {
					setMsg('ERR: ' + err.message);
				}
			})
			.finally(() => setPost(false));
	}

	const ChangeFn = (type, id) => FormInputChangeFn(data, setData, type, id);
	const Field = (type, name, id) => FormInputField(type, name, data[id], ChangeFn(type, id), { id: id });
	const FieldArr = arr => Field(arr[0], arr[1], arr[2]);

	return (<>
		{ type === 'COMPLAINT' && <h1>Complaint Submission</h1> }
		{ type === 'CRIME_SCENE' && <h1>Crime Scene Report</h1> }
		{msgs.map((x, i) => <p key={i} style={{ textAlign: 'center' }}>{x}</p>)}
		<div style={{ maxWidth: '500px', margin: '0 auto' }}>
			{subm_fields_common.map(ent => FieldArr(ent))}
			{subm_fields[type].map(ent => FieldArr(ent))}
			<button onClick={submit} disabled={post} style={{ width: '100%' }}>Submit</button>
		</div>
	</>)
}

export const ComplaintSubmitForm = props => SubmissionSubmitForm({ ...props, type: 'COMPLAINT' });
export const CrimeSubmitForm = props => SubmissionSubmitForm({ ...props, type: 'CRIME_SCENE' });

export function SubmissionFrame({ subm, compact, ...props }) {
	const meta_fields = [
		['text', 'Type', 'submission_type'],
		['text', 'Status', 'status'],
		['number', 'Stage', 'current_stage'],
		['datetime', 'Created at', 'created_at'],
	];
	const type = subm.submission_type;

	const Process = data => (type, name, id) => FormField(type, name, data[id], { key: id, compact });
	const ProcessArr = data => (ent) => Process(data)(...ent);
	return (
		<div {...props}>
			<div className='item'>
				{meta_fields.map(ProcessArr(subm))}
				{subm_fields_common.map(ProcessArr(subm.target))}
				{subm_fields[type].map(ProcessArr(subm.target))}
			</div>
		</div>
	);
}

export function SubmissionList({ title, path }) {
	const [str, setStr] = useState('Retrieving...')
	const [phase, setPhase] = useState(0);
	const [compact, setCompact] = useState(true);
	const [subm_list, set_subm_list] = useState([]);

	const req = () => {
		setPhase(1);
		session.get(path)
			.then(res => {
				const arr = res.data;
				for (const subm of arr) {
					const type = subm.submission_type;
					if (type === 'COMPLAINT' && subm.target.complainant_national_ids === undefined)
						subm.target.complainant_national_ids = subm.target.complainants;
					if (type === 'COMPLAINT')
						subm.target.complainant_national_ids = subm.target.complainant_national_ids.map(x => [x]);
					if (type === 'CRIME_SCENE')
						subm.target.witnesses = subm.target.witnesses.map(obj => [obj.phone_number, obj.national_id]);
				}
				setStr('Retrieved successfuly')
				set_subm_list(arr);
			})
			.catch(err => {
				if (err.response)
					setStr('ERR: ' + err.status);
				else
					setStr('Failed: ' + err.message);
			})
			.finally(() => setPhase(2));
	}

	if (phase === 0)
		req();

	const eleWidth = compact? 450: 550;
	return (<>
		<h1>{title}</h1>
		<p style={{ textAlign: 'center' }}>{str}</p>
		<button disabled={phase !== 2} onClick={() => { setStr('Retrying...'); req(); }}>Retry</button>
		<label>
			<input type='checkbox' checked={compact} onChange={() => setCompact(!compact)} />
			Compact View
		</label>
		<ResponsiveGrid eleWidth={eleWidth}>
			{subm_list.map((subm, i) => (<SubmissionFrame style={{ width: eleWidth }} key={i} compact={compact} subm={subm}/>))}
		</ResponsiveGrid>
	</>)
}

export const MySubmissions = props => SubmissionList({ ...props, title: 'My Submissions', path: '/api/submission/mine/' })
export const InboxSubmissions = props => SubmissionList({ ...props, title: 'Inbox Submissions', path: '/api/submission/inbox/' })

export default SubmissionSubmitForm
