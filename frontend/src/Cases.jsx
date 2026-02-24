import { useState, useEffect, useContext } from 'react'
import { useNavigate, useLocation } from 'react-router'
import { form_list_decode, FormField, GenericList, ListCompactCtx } from './Forms'
import session from './session'

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
export const CaseListSafe = ({ ...props }) => CaseList({ ...props, safeOnly: true });

export default CaseList
