import { useState, useEffect, useContext } from 'react'
import { useNavigate } from 'react-router'
import { FormInputField, FormInputChangeFn, FormField, SimpleInputField, GenericList, ListCompactCtx } from './Forms'
import { session, error_msg, error_msg_list } from './session'

// type, name, id
const evi_fields_auto = [
	['number', 'PK', 'id'],
	['datetime', 'Created at', 'created_at'],
	['number', 'Recorder PK', 'recorder'],
];
const evi_fields_common = [
	// ['number', 'Case PK', 'case'],
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

export function EvidenceSubmitForm({ returnTo, case_id }) {
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
		
		formData.append("case", case_id)
		console.log(formData)

		session.post('/api/evidence/', formData)
			.then(res => {
				setMsg('Submit successful');
				setData(defaultData());
				if (returnTo) navigate(returnTo);
			})
			.catch(err => setMsgs(error_msg_list(err)))
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
			{SimpleInputField('Type', (
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

export function EvidenceFrame({ evi, onSelect, className, ...props }) {
	const compact = useContext(ListCompactCtx);
	const Process = (type, name, id) => FormField(type, name, evi[id], { key: id, compact });
	const ProcessArr = (ent) => Process(...ent);
	return (
		<div className={className || 'item'} {...props}>
			{Process('text', 'Type', 'type')}
			{!compact && evi_fields_auto.map(ProcessArr)}
			{evi_fields_common.map(ProcessArr)}
			{evi_fields[evi.type].map(ProcessArr)}
			{ onSelect && <button onClick={onSelect}>Select</button> }
		</div>
	)
}

export const evi_decode = evi => {
	const ans = { ...evi }
	for (const [type, info] of Object.entries(evi_field_info)) if (evi.resource_type == info.res_type)
		ans.type = type;
	if (ans.type === 'bio')
		ans.uploaded_images = ans.images.map(ent => ent.image);
	return ans;
}


export const EvidenceList = ({ list, title, onReload, onReturn, onSelect }) => (
	<GenericList title={title} onReload={onReload} onReturn={onReturn}>
		{list.map((evi, i) => (<EvidenceFrame key={i} evi={evi} onSelect={onSelect && (() => onSelect(evi))}/>))}
	</GenericList>
);

export default EvidenceList
