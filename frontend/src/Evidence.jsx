import { useState } from 'react'
import { useNavigate } from 'react-router'
import session from './session.jsx'

// type, name, id
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
	bio: [
		['files', 'Images', 'uploaded_images'],
	],
	other: [
	],
};
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

	const changeFn = (type, name) => e => {
		const data2 = {...data};
		if (type === 'file') {
			data2[name] = e.target.files[0];
		} else if (type === 'files') {
			if (typeof e === 'number')
				data2[name] = [].concat(data[name].slice(0, e), data[name].slice(e + 1));
			else
				data2[name] = [...data[name], e];
		} else {
			if (name === 'type')
				data2.media_file = '';
			data2[name] = e.target.value;
		}
		setData(data2);
	}
	const chain = (...fns) => () => fns.forEach(fn => fn());
	const setMsg = msg => setMsgs([msg]);

	const submit = () => {
		setMsg('Awaiting response...');
		setPost(true);

		const formData = new FormData();
		formData.append('type', data.type);
		for (const ents of [evi_fields_common, evi_fields[data.type]]) for (const ent of ents) {
			const id = ent[2];
			if (Array.isArray(data[id]))
				data[id].forEach(v => formData.append(id, v));
			else
				formData.append(id, data[id]);
		}

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

	const Field5 = (type, name, id, value, onChange) => {
		const Simple = body => (
			<div key={id}>
				<label htmlFor={id}>{name}: </label>
				{body}
			</div>
		);
		if (type === 'textarea')
			return Simple((<textarea id={id} value={value} onChange={onChange}/>));
		else if (type === 'file')
			return Simple((<input id={id} type={'file'} onChange={onChange}/>));
		else if (type === 'files')
			return (
				<div key={id} style={{ display: 'flex', flexDirection: 'row' }}>
					<label htmlFor={id}>{name}: </label>

					<input
						id={id}
						type={'file'}
						style={{ display: 'none' }}
						onChange={e => e.target.files && onChange(e.target.files[0])}
					/>

					<div style={{ flex: 1, display: 'flex', flexDirection: 'column', textAlign: 'left' }}>
						<button onClick={() => document.getElementById(id).click()}>Add</button>

						{value && value.map((file, i) => (
							<div
								key={i}
								style={{ display: 'flex', flexDirection: 'row' }}
							>
								<p style={{ flex: 1 }}>{file.name}</p>
								<button onClick={() => onChange(i)}>Remove</button>
							</div>
						))}
					</div>
				</div>
			);
		else
			return Simple((<input id={id} type={type} value={value} onChange={onChange}/>));
	};
	const Field = (type, name, id) => Field5(type, name, id, data[id], changeFn(type, id));
	const FieldArr = arr => Field(arr[0], arr[1], arr[2]);

	return (<>
		<h1>Evidence Submission</h1>
		{msgs.map((x, i) => <p key={i}>{x}</p>)}
		<div style={{ display: 'flex', flexDirection: 'column' }}>
			<select value={data.type} onChange={changeFn('text', 'type')}>
				{evi_types.map(type => (<option key={type} id={type}>{type}</option>))}
			</select>
			{evi_fields_common.map(ent => FieldArr(ent))}
			{evi_fields[data.type].map(ent => FieldArr(ent))}
			<button onClick={submit} disabled={post}>Submit</button>
		</div>
	</>)
}

export default EvidenceSubmitForm
