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
	other: [],
};
const evi_types = [...Object.keys(evi_fields)];

export function EvidenceSubmitForm({ returnTo }) {
	const [data, setData] = useState(() => {
		const obj = {type: evi_types[0]};
		for (const ent of evi_fields_common)
			obj[ent[2]] = '';
		for (const type of evi_types) for (const ent of evi_fields[type])
			obj[ent[2]] = '';
		return obj;
	});
	const [post, setPost] = useState(false);
	const [msgs, setMsgs] = useState([]);
	const navigate = useNavigate();

	const changeFn = name => e => {
		const data2 = {...data};
		data2[name] = e.target.value;
		setData(data2);
	}
	const setMsg = msg => setMsgs([msg]);

	const submit = () => {
		setMsg('Awaiting response...');
		setPost(true);

		const subdata = {type: data.type};
		for (const ent of evi_fields_common)
			subdata[ent[2]] = data[ent[2]];
		for (const ent of evi_fields[data.type])
			subdata[ent[2]] = data[ent[2]];

		session.post('/api/evidence/', subdata)
			.then(res => {
				setMsg('Submit successful');
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

	const Field5 = (type, name, id, value, onChange) => (<div key={id}>
		<label htmlFor={id}>{name}: </label>
		{
			  type === 'textarea' ? (<textarea id={id} value={value} onChange={onChange}/>)
			: /* else */            (<input id={id} type={type} value={value} onChange={onChange}/>)
		}
	</div>);
	const Field = (type, name, id) => Field5(type, name, id, data[id], changeFn(id));
	const FieldArr = arr => Field(arr[0], arr[1], arr[2]);

	return (<>
		<h1>Evidence Submission</h1>
		{msgs.map((x, i) => <p key={i}>{x}</p>)}
		<div style={{ display: 'flex', flexDirection: 'column' }}>
			<select onChange={changeFn('type')}>
				{evi_types.map(type => (<option key={type} id={type}>{type}</option>))}
			</select>
			{evi_fields_common.map(ent => FieldArr(ent))}
			{evi_fields[data.type].map(ent => FieldArr(ent))}
			<button onClick={submit} disabled={post}>Submit</button>
		</div>
	</>)
}

export default EvidenceSubmitForm
