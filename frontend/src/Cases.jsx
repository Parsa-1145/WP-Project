import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router'
import { form_list_map, FormField, GenericList } from './Forms'
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
	['list Phone ID', 'Witnesses', 'witnesses'],
	['list ID', 'Complainants', 'complainant_national_ids'],
];

export const case_decode = cas => form_list_map(cas, { witnesses: ['phone_number', 'national_id'], complainant_national_ids: ''});

export function CaseFrame({ cas, ...props }) {
	const Process = (type, name, id) => FormField(type, name, cas[id], { key: id });
	const ProcessArr = ent => Process(...ent);
	return (
		<div className='item' {...props}>
			{case_fields.map(ProcessArr)}
		</div>
	);
}

export const CaseList = ({ list, title, onReload, onReturn }) => (
	<GenericList title={title} onReload={onReload} onReturn={onReturn}>
		{list.map((cas, i) => (<CaseFrame key={i} cas={cas}/>))}
	</GenericList>
);

export default CaseList
