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
	identity: [
		['text', 'Full Name', 'full_name'],
		['keyvalue', 'Details', 'details'],
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
		} else if (type === 'keyvalue') {
			if (typeof e === 'number')
				data2[name] = [].concat(data[name].slice(0, e), data[name].slice(e + 1));
			else {
				data2[name] = [...data[name]];
				data2[name][e[0]] = [e[1], e[2]];
			}
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
		const formData = new FormData();
		formData.append('type', data.type);
		for (const ents of [evi_fields_common, evi_fields[data.type]]) for (const ent of ents) {
			const [type,, id] = ent;
			if (type === 'keyvalue') {
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

	const SimplePair = ({ name, children, id }) => (
		<div style={{ position: 'relative' }}>
			<label style={{ position: 'absolute', left: 0 }} htmlFor={id}>{name}: </label>
			<div style={{ marginLeft: '25%', textAlign: 'left' }}>
				{children}
			</div>
		</div>
	);

	const Field5 = (type, name, id, value, onChange) => {
		const Simple = body => (<SimplePair name={name} key={id} id={id}>{body}</SimplePair>);
		if (type === 'textarea')
			return Simple((<textarea id={id} value={value} onChange={onChange}/>));
		else if (type === 'file')
			return Simple((<input id={id} type={'file'} onChange={onChange}/>));
		else if (type === 'files')
			return (
				<div key={id} style={{ position: 'relative' }}>
					<label htmlFor={id} style={{ position: 'absolute', left: 0 }}>{name}: </label>

					<input
						id={id}
						type={'file'}
						style={{ display: 'none' }}
						onChange={e => e.target.files && onChange(e.target.files[0])}
					/>

					<div style={{ flex: 1, display: 'flex', flexDirection: 'column', textAlign: 'left', marginLeft: '25%' }}>
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
		else if (type === 'keyvalue')
			return (
				<div key={id} style={{ position: 'relative' }}>
					<label htmlFor={id} style={{ position: 'absolute', left: 0 }}>{name}: </label>

					<div id={id} style={{ flex: 1, display: 'flex', flexDirection: 'column', textAlign: 'left', marginLeft: '25%' }}>
						{value && Object.entries(value).map((ent, i) => (
							<div
								key={i}
								style={{ display: 'flex', flexDirection: 'row' }}
							>
								<input value={value[i][0]} placeholder='Key' type='text' onChange={e => onChange([i, e.target.value, value[i][1]])}/>
								<input value={value[i][1]} placeholder='Value' type='text' onChange={e => onChange([i, value[i][0], e.target.value])} style={{ flex: 1 }}/>
								<button onClick={() => onChange(i)}>Remove</button>
							</div>
						))}

						<button onClick={() => onChange([value.length, '', ''])}>New</button>
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
		{msgs.map((x, i) => <p key={i} style={{ textAlign: 'center' }}>{x}</p>)}
		<div style={{ maxWidth: '500px', margin: '0 auto' }}>
			<SimplePair name='Type' id='type'>
				<select value={data.type} onChange={changeFn('text', 'type')}>
					{evi_types.map(type => (<option key={type} id={type}>{type}</option>))}
				</select>
			</SimplePair>
			{evi_fields_common.map(ent => FieldArr(ent))}
			{evi_fields[data.type].map(ent => FieldArr(ent))}
			<button onClick={submit} disabled={post} style={{ width: '100%' }}>Submit</button>
		</div>
	</>)
}

export default EvidenceSubmitForm
