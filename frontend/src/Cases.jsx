import { useState, useEffect, useContext } from 'react'
import { useNavigate, useLocation } from 'react-router'
import { form_list_decode, form_list_encode, FormInputField, FormInputChangeFn, FormField, GenericList, ListCompactCtx } from './Forms'
import { session, error_msg_list } from './session'

// due to case being a keyword, we use cas instead

// type, name, id
const case_fields = [
	['number', 'ID', 'id'],
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

export function CaseFrame({ cas, safeOnly, ...props }) {
	const compact = useContext(ListCompactCtx);
	const fields = safeOnly? case_fields.filter(([,, id]) => case_safe_fields.includes(id)): case_fields;

	const Process = (type, name, id) => FormField(type, name, cas[id], { key: id, compact });
	const ProcessArr = ent => Process(...ent);
	return (
		<div className='item' {...props}>
			{fields.map(ProcessArr)}
		</div>
	);
}

export const CaseList = ({ list, title, onReload, onReturn, safeOnly }) => (
	<GenericList title={title} onReload={onReload} onReturn={onReturn}>
		{list.map((cas, i) => (<CaseFrame key={i} cas={cas} safeOnly={safeOnly}/>))}
	</GenericList>
);

export default CaseList
