import { useState, useEffect, useContext } from 'react'
import { useNavigate } from 'react-router'
import { FormInputField, FormInputChangeFn, FormField, SimpleInputField, GenericList, ListCompactCtx } from './Forms'
import { session, error_msg, error_msg_list } from './session'
import { CustomSelect } from './CustomSelect'
import { NormalizationType, normalizeString, formatDate } from './utils'

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

const getEvidenceStatusBadgeStyle = statusRaw => {
	const status = String(statusRaw || '').toUpperCase();
	if (!status)
		return {
			color: 'var(--c-text-muted)',
			borderColor: 'var(--c-border)',
			backgroundColor: 'var(--c-surface-2)',
		};

	if (['REJECTED', 'GUILTY', 'FAILED', 'NOT_VERIFIED'].includes(status))
		return {
			color: 'var(--c-danger)',
			borderColor: 'var(--c-danger)',
			backgroundColor: 'rgba(255, 107, 107, 0.1)',
		};

	if (['APPROVED', 'ACCEPTED', 'CLEARED', 'VERIFIED'].includes(status))
		return {
			color: 'var(--c-primary)',
			borderColor: 'var(--c-primary)',
			backgroundColor: 'rgba(92, 255, 157, 0.1)',
		};

	if (['PENDING', 'PENDING_ASSESSMENT', 'IN_REVIEW'].includes(status))
		return {
			color: 'var(--c-warning)',
			borderColor: 'var(--c-warning)',
			backgroundColor: 'rgba(255, 209, 102, 0.1)',
		};

	return {
		color: 'var(--c-text-muted)',
		borderColor: 'var(--c-border)',
		backgroundColor: 'var(--c-surface-2)',
	};
};

export function EvidenceSubmitForm({ returnTo, case_id, onSubmitted }) {
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
				if (onSubmitted) onSubmitted(res);
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
		{msgs.map((x, i) => <p key={i} style={{ textAlign: 'center' }}>{x}</p>)}
		<div className='flex flex-col gap-7'>
			{SimpleInputField('Type', (
				<CustomSelect
					id="evidence_type"
					name="type"
					value={data.type}
					onChange={ChangeFn('text', 'type')}
					options={evi_types.map(type => ({ key: type, value: type }))}
					className="w-full"
					buttonClassName="custom-select-button"
					menuClassName="custom-select-menu"
					optionClassName="custom-select-option"
				/>
			), { id: 'type' })}
			<div className='flex flex-col gap-2'>
				{evi_fields_common.map(ent => FieldArr(ent))}
				{evi_fields[data.type].map(ent => FieldArr(ent))}
			</div>

			<button className='btn w-full' onClick={submit} disabled={post}>Submit</button>
		</div>
	</>)
}

export function EvidenceFrame({ evi, onSelect, className, ...props }) {
	const compact = useContext(ListCompactCtx);
	const Process = (type, name, id) => FormField(type, name, evi[id], { key: id, compact });
	const ProcessArr = (ent) => Process(...ent);
	const frameClassName = className || 'border-1 border-(--c-border) bg-(--c-surface) flex flex-col gap-2 h-full p-2 max-h-80 overflow-hidden';
	const reviewStatusRaw = evi.status
		? String(evi.status).toUpperCase()
		: evi.approval_status
			? String(evi.approval_status).toUpperCase()
			: (typeof evi.is_verified === 'boolean'
				? (evi.is_verified ? 'VERIFIED' : 'NOT_VERIFIED')
				: '');
	const reviewStatusStyle = getEvidenceStatusBadgeStyle(reviewStatusRaw);
	const reviewStatusLabel = reviewStatusRaw === 'NOT_VERIFIED'
		? 'Not Verified'
		: normalizeString(reviewStatusRaw, NormalizationType.LOWER_CASE);
	return (
		<>
			<div className={frameClassName} {...props}>
				<div className='flex flex-col gap-2'>
					<div className='flex flex-row items-start gap-2'>
						<h2 className='text-left grow'>
							{evi.title}
						</h2>
						<div
							className='border-1 px-2 py-0.5 text-sm whitespace-nowrap'
							style={{
								borderColor: 'var(--c-primary)',
								backgroundColor: 'rgba(92, 255, 157, 0.1)',
								color: 'var(--c-primary)',
							}}
						>
							{normalizeString(evi.type, NormalizationType.LOWER_CASE)}
						</div>
						{reviewStatusRaw
							? (
								<div className='border-1 px-2 py-0.5 text-sm whitespace-nowrap' style={reviewStatusStyle}>
									{reviewStatusLabel}
								</div>
							)
							: null}
					</div>
					<h3 className='text-(--c-text-muted) m-0'>
						{evi.description}
					</h3>
					{evi.created_at
						? <div className='text-sm text-[var(--c-text-muted)]'>recorded: {formatDate(evi.created_at)}</div>
						: null}
				</div>
				<div className='grow min-h-0 overflow-y-auto pr-1'>
					{evi_fields[evi.type].map(ProcessArr)}
				</div>
				{onSelect
					? (
						<div className='w-full text-right'>
							<button className='btn' onClick={onSelect}>select</button>
						</div>
					)
					: null}
			</div>
		</>
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
