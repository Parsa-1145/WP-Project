import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router'
import { FormInputField, FormInputChangeFn, FormField, SimpleField } from './Forms'
import session from './session'

// type, name, id
const evi_fields_auto = [
	['number', 'PK', 'id'],
	['datetime', 'Created at', 'created_at'],
	['number', 'Recorder PK', 'recorder'],
];
const evi_fields_common = [
	['number', 'Case PK', 'case'],
	['text', 'Title', 'title'],
	['textarea', 'Description', 'description'],
];
const evi_fields = {
	witness: [
		['textarea', 'Transcript', 'transcript'],
		['file', 'Media', 'media_file'],
	],
	vehicle: [
		['text', 'Model', 'model_name'],
		['text', 'Color', 'color'],
		['text', 'Plate Number', 'plate_number'],
		['text', 'Serial Number', 'serial_number'],
	],
	identity: [
		['text', 'Full Name', 'full_name'],
		['list Key Value', 'Details', 'details'],
	],
	bio: [
		['files', 'Images', 'uploaded_images'],
	],
	other: [
	],
};
const evi_field_info = {
	witness: { res_type: 'WitnessEvidence' },
	vehicle: { res_type: 'VehicleEvidence' },
	identity: { res_type: 'IdentityEvidence' },
	bio: { res_type: 'BioEvidence' },
	other: { res_type: 'OtherEvidence' },
}
const evi_types = [...Object.keys(evi_fields)];

export function EvidenceSubmitForm({ returnTo }) {
	const defaultData = () => {
		const obj = {type: evi_types[0]};
		for (const ent of evi_fields_common)
			obj[ent[2]] = '';
		for (const type of evi_types) for (const ent of evi_fields[type])
			obj[ent[2]] = '';
		return obj;
	};
	const [data, setData] = useState(defaultData);
	const [post, setPost] = useState(false);
	const [msgs, setMsgs] = useState([]);
	const navigate = useNavigate();
	const setMsg = msg => setMsgs([msg]);

	const submit = () => {
		const formData = new FormData();
		formData.append('type', data.type);
		for (const ents of [evi_fields_common, evi_fields[data.type]]) for (const ent of ents) {
			const [type,, id] = ent;
			if (type === 'list Key Value') {
				const res = {};
				for (const kv of data[id]) {
					if (res[kv[0]] !== undefined) {
						setMsg('Duplicate key in key-value pairs');
						return;
					}
					res[kv[0]] = kv[1];
				}
				formData.append(id, JSON.stringify(res));
			} else if (type === 'files')
				data[id].forEach(v => formData.append(id, v));
			else
				formData.append(id, data[id]);
		}

		setPost(true);
		setMsg('Awaiting response...');

		session.post('/api/evidence/', formData)
			.then(res => {
				setMsg('Submit successful');
				setData(defaultData());
				if (returnTo) navigate(returnTo);
			})
			.catch(err => {
				if (err.response) {
					if (typeof err.response.data === 'object')
						setMsgs(Object.entries(err.response.data).map(xy => 'ERR: ' + xy[0] + ' - ' + xy[1]));
					else
						setMsg('ERR: ' + err.response.data);
				} else {
					setMsg('ERR: ' + err.message);
				}
			})
			.finally(() => setPost(false));
	}

	const ChangeFn = (type, id) => e => {
		if (id === 'type')
			data.media_file = ''; // kinda a hack
		FormInputChangeFn(data, setData, type, id)(e);
	}
	const Field = (type, name, id) => FormInputField(type, name, data[id], ChangeFn(type, id), { id: id });
	const FieldArr = arr => Field(arr[0], arr[1], arr[2]);

	return (<>
		<h1>Evidence Submission</h1>
		{msgs.map((x, i) => <p key={i} style={{ textAlign: 'center' }}>{x}</p>)}
		<div style={{ maxWidth: '500px', margin: '0 auto' }}>
			{SimpleField('Type', (
				<select value={data.type} onChange={ChangeFn('text', 'type')}>
					{evi_types.map(type => (<option key={type} id={type}>{type}</option>))}
				</select>
			), { id: 'type' })}
			{evi_fields_common.map(ent => FieldArr(ent))}
			{evi_fields[data.type].map(ent => FieldArr(ent))}
			<button onClick={submit} disabled={post} style={{ width: '100%' }}>Submit</button>
		</div>
	</>)
}

export function EvidenceFrame({ evi, compact, ...props }) {
	const Process = (type, name, id) => FormField(type, name, evi[id], { key: id, compact });
	const ProcessArr = (ent) => Process(...ent);
	return (
		<div {...props} className='item'>
			{Process('text', 'Type', 'type')}
			{!compact && evi_fields_auto.map(ProcessArr)}
			{evi_fields_common.map(ProcessArr)}
			{evi_fields[evi.type].map(ProcessArr)}
		</div>
	)
}

export function EvidenceList({}) {
	const [str, setStr] = useState('Retrieving...')
	const [phase, setPhase] = useState(0);
	const [compact, setCompact] = useState(true);
	const [evi_list, set_evi_list] = useState([]);

	const req = () => {
		setPhase(1);
		session.get('/api/evidence/')
			.then(res => {
				try {
					const arr = res.data;
					for (const evi of arr) {
						for (const info of Object.entries(evi_field_info)) if (evi.resource_type == info[1].res_type)
							evi.type = info[0];
						if (evi.type === 'bio')
							evi.uploaded_images = evi.images.map(ent => ent.image);
					}
					setStr('Retrieved successfuly')
					set_evi_list(arr);
				} catch (e) {
					setStr('Exception: ' + e.toString());
				}
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

	const [width, setWidth] = useState(window.innerWidth);
	useEffect(() => {
		const handle = () => setWidth(window.innerWidth);
		window.addEventListener('resize', handle);
		return () => window.removeEventListener('resize', handle);
	}, []);
	const eviWidth = compact? 450: 550;
	const rowSize = Math.max(1, Math.floor(width * 0.9 / eviWidth));
	const divWidth = eviWidth * rowSize;

	return (<>
		<h1>Evidence List</h1>
		<p style={{ textAlign: 'center' }}>{str}</p>
		<button disabled={phase !== 2} onClick={() => { setStr('Retrying...'); req(); }}>Retry</button>
		<label>
			<input type='checkbox' checked={compact} onChange={() => setCompact(!compact)} />
			Compact View
		</label>
		<div style={{
			display: 'grid',
			gridTemplateColumns: 'repeat(' + rowSize + ', 1fr)',
			gridTemplateRows: 'auto',
			width: divWidth,
		}}>
			{evi_list.map((evi, i) => (<EvidenceFrame key={i} compact={compact} evi={evi}/>))}
		</div>
	</>)
}

export default EvidenceList
