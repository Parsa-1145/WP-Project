import { useState, useEffect, createContext, useContext, useRef } from 'react'
import { formatDate } from './utils';

const FORM_DATETIME_TZ = '+03:30';

const toDatetimeLocalValue = (value) => {
	if (typeof value !== 'string')
		return '';

	const trimmed = value.trim();
	if (!trimmed)
		return '';

	const match = trimmed.match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})/);
	if (match)
		return `${match[1]}T${match[2]}`;

	return trimmed.slice(0, 16);
};

export const SimpleInputField = (name, body, { id, key, compact, style }) => {
	if (key === undefined) key = id;
	return (
		<div key={key} className='flex flex-col gap-1 grow'>
			<div className='grow flex flex-row gap-2 items-center'>
				<span className='datetime-prefix'>&gt;</span>
				<label htmlFor={id} className='grow'>{name} </label>
			</div>
			{body}
		</div>
	);
};

export const SimpleField = (name, body, { id, key, compact, style }) => {
	if (key === undefined) key = id;
	return (
		<div key={key} className='grid grid-cols-2'>
			<label htmlFor={id} className='grow'>{name} : </label>
			{body}
		</div>
	);
};

const is_list = (type) => typeof type === 'string' && type.slice(0, 5) == 'list ';

const parse_list = (type, input) =>
	type
		.split(' ')
		.slice(1)
		.filter(e => !input || e[0] != '!')
		.filter(e => input || e[0] != '.')
		.map(e => e[0] == '!' || e[0] == '.'? e.slice(1): e)
		.map(e => e.replaceAll('_', ' '))

export const FormInputField = (type, name, value, onChange, { id, key }) => {
	if (key === undefined) key = id;

	const Simple = body => SimpleInputField(name, body, { id, key });

	if (type === 'textarea')
		return Simple((<textarea id={id} value={value} onChange={onChange} className='input  w-full'/>));

	else if (type === 'file')
		return Simple((<input id={id} type={'file'} onChange={onChange} />));

	else if (type === 'files')
		return (
			<div key={key} style={{ position: 'relative' }}>
				<label htmlFor={id} style={{ position: 'absolute', left: 0 }}>{name}: </label>

				<input
					id={id}
					type={'file'}
					style={{ display: 'none' }}
					onChange={e => e.target.files && onChange(e.target.files[0])}
				/>

				<div style={{ flex: 1, display: 'flex', flexDirection: 'column', textAlign: 'left', marginLeft: '180px' }}>
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

	else if (type === 'datetime') {
		const valueSmall = toDatetimeLocalValue(value);
		return Simple((
				<div className='flex flex-row'>
					<input
						id={id}
						type='datetime-local'
						value={valueSmall}
						onChange={onChange}
						className='input grow'
					/>
					{/* <span className='datetime-tz'>[UTC{FORM_DATETIME_TZ}]</span> */}
				</div>
		));
	}

	else if (is_list(type)) {
		const eles = parse_list(type, true);
		return (
			<div key={id} className='flex flex-col'>
				<div className='grow flex flex-row gap-2 items-center'>
					<span className='datetime-prefix'>&gt;</span>
					<label htmlFor={id} className='grow'>{name} </label>
				</div>
				<div id={id} className='flex flex-col gap-2 border-1 border-dotted p-2'>
					{value && value.map((ent, i) => (
						<div
						key={i}
						className='w-full flex flex-row gap-2'
						>
							{eles.map((ele, j) => (
								<input key={j} value={ent[j]} placeholder={ele} type='text'
								 onChange={e => {
									const ent2 = [...ent];
									ent2[j] = e.target.value;
									onChange([i, ent2])
								}} 
								className='grow input'
								/>
							))}
							<button className='btn btn-sm' onClick={() => onChange(i)}>x</button>
						</div>
					))}

					<button className='btn btn-sm w-full' onClick={() => onChange([value.length, eles.map(() => '')])}>Add</button>
				</div>
			</div>
		);
	}

	else
		return Simple((<input id={id} type={type} value={value} onChange={onChange} className='input w-full'/>));
};

export const FormInputChangeFn = (data, setData, type, name) => e => {
	const data2 = {...data};
	if (type === 'file')
		data2[name] = e.target.files[0];

	else if (type === 'files') {
		if (typeof e === 'number')
			data2[name] = [].concat(data[name].slice(0, e), data[name].slice(e + 1));
		else
			data2[name] = [...data[name], e];
	}

	else if (type === 'datetime') {
		data2[name] = e.target.value ? `${e.target.value}:00${FORM_DATETIME_TZ}` : '';
	}

	else if (is_list(type)) {
		if (typeof e === 'number')
			data2[name] = [].concat(data[name].slice(0, e), data[name].slice(e + 1));
		else {
			data2[name] = [...data[name]];
			data2[name][e[0]] = e[1];
		}
	}

	else
		data2[name] = e.target.value;

	setData(data2);
}

export const ListCompactCtx = createContext(false);

export const FormField = (type, name, value, { id, key, compact }) => {
	if (key === undefined) key = id;

	if (!compact) {
		const imgStyle = { display: 'block', margin: '0 auto', maxWidth: '500px' };

		if (type === 'file') // image
			return (<img key={key} src={value} style={imgStyle}/>);

		else if (type === 'files') // images
			return (<div key={key}>{value.map((src, i) => (<img key={i} src={src} style={imgStyle}/>))}</div>);

		else if (type === 'list Key Value')
			return (<div key={key}>{Object.entries(value).map((kv, i) => SimpleField(kv[0], (<p>{kv[1]||'<empty>'}</p>), { key: i }))}</div>);

		else if (is_list(type)) {
			const enames = parse_list(type, false);
			return (
				<div key={key}>
					<div>{name}</div>
					<div style={{ display: 'flex', flexDirection: 'row' }}>
						{enames.map((ename, j) => (<div key={j} style={{ flex: 1, textAlign: 'left' }}><strong>{ename}</strong></div>))}
					</div>
					{value.map((ent, i) => (
						<div key={i} style={{ display: 'flex', flexDirection: 'row' }}>
							{ent.map((ele, j) => (<div key={j} style={{ flex: 1, textAlign: 'left' }}>{ele || '<empty>'}</div>))}
						</div>
					))}
					<p></p>
				</div>
			);
		}

		else{
			if (type === 'datetime')
				value = formatDate(value, 
			{options: {hour: '2-digit', minute: '2-digit', year: 'numeric',month: 'short',day: 'numeric'},
			showRelative:true});
			return SimpleField(name, (<p>{value||'<empty>'}</p>), { id, key });
		}
	}

	else {
		const imgStyle = { display: 'block', margin: '0 auto',
			maxWidth: compact >= 2? '250px': '400px',
			maxHeight: compact >= 2? '150px': '300px',
		};
		const divStyle = compact >= 2? { fontSize: '10pt' }: {};

		if (type === 'file') // image
			return (<img key={key} src={value} style={imgStyle}/>);

		else if (type === 'files') { // images
			let imgs = value;
			if (compact >= 2) imgs = imgs.slice(0, 1);
			return (<div key={key}>{imgs.map((src, i) => (<img key={i} src={src} style={imgStyle}/>))}</div>);
		}

		else if (type === 'list Key Value')
			return (<div key={key} style={divStyle}>{Object.entries(value).map((kv, i) => SimpleField(kv[0], (<div>{kv[1]||'<empty>'}</div>), { key: i, compact }))}</div>);

		else if (is_list(type))
			return SimpleField(name, (<pre>{value.map(ent => ent.slice(0, 2).map(ele => ele||'<empty>').join(' - ')).join('\n') || '<empty>'}</pre>), { id, key, compact, style: divStyle });

		else {
			if (type === 'textarea')
				value = value.length > 128? value.slice(0, 128) + '...': value;
			if (type === 'datetime')
				value = formatDate(value, 
			{options: {hour: '2-digit', minute: '2-digit', year: 'numeric',month: 'short',day: 'numeric'},
			showRelative:false});
			return SimpleField(name, (<div>{value||'<empty>'}</div>), { id, key, style: divStyle, compact });
		}
	}
}

export const ResponsiveGrid = ({ eleWidth, children, ...props }) => {
	// const containerRef = useRef(null);
	// const [width, setWidth] = useState(window.innerWidth);
	// useEffect(() => {
	// 	const parentElement = containerRef.current?.parentElement;
	// 	if (!parentElement)
	// 		return;

	// 	const updateWidth = () => setWidth(parentElement.clientWidth || window.innerWidth * 0.9);
	// 	updateWidth();

	// 	if (typeof ResizeObserver !== 'undefined') {
	// 		const observer = new ResizeObserver(updateWidth);
	// 		observer.observe(parentElement);
	// 		return () => observer.disconnect();
	// 	}

	// 	window.addEventListener('resize', updateWidth);
	// 	return () => window.removeEventListener('resize', updateWidth);
	// }, []);
	// const rowSize = Math.max(1, Math.floor(width / eleWidth));
	// const divWidth = eleWidth * rowSize;
	return (
		// <div ref={containerRef} style={{
		// 	display: 'grid',
		// 	gridTemplateColumns: 'repeat(' + rowSize + ', 1fr)',
		// 	gridTemplateRows: 'auto',
		// 	width: divWidth,
		// 	margin: '0 auto',
		// 	gap:'0.5rem'
		// }} {...props}>
		// 	{children}
		// </div>
		<div className='flex flex-row flex-wrap gap-2'>
			{children}
		</div>
	);
}

export const form_list_decode = (obj, eles) => {
	const ans = {};
	for (const key in obj) {
		const definition = eles[key];
		if (definition === '')
			ans[key] = obj[key].map(ent => [ent]);
		else if (Array.isArray(definition))
			ans[key] = obj[key].map(ent => eles[key].map(id => ent[id]));
		else
			ans[key] = obj[key];
	}
	return ans;
}
export const form_list_encode = (obj, eles) => {
	const ans = {};
	for (const key in obj) {
		const definition = eles[key];
		if (definition === '')
			ans[key] = obj[key].map(([ent]) => ent);
		else if (Array.isArray(definition))
			ans[key] = obj[key].map(ent => {
				res = {};
				for (let i = 0; i < eles.length; i++)
					res[eles[i]] = ent[i];
				return res;
			})
		else
			ans[key] = obj[key];
	}
	return ans;
}


export function GenericList({ children, title, onReload, onReturn, msg, description=null }) {
	const [compact, setCompact] = useState(true);
	const eleWidth = compact? 450: 550;
	return (<>
		<div className='flex flex-col'>
			<div className='flex flex-row shrink w-full gap-2'>
				<div className='grow'>
					<h2 className='text-left'>
						{title}
					</h2>
					{description != null?<h3 className='text-left'>{description}</h3>:null}
				</div>
				<div className='flex flex-col'>
					<label>
						<input type='checkbox' checked={compact} onChange={() => setCompact(!compact)} />
						Compact View
					</label>
					{ onReload && (<button onClick={onReload}>Reload</button>) }
					{ onReturn && (<button onClick={onReturn}>Return</button>) }
				</div>
			</div>
		</div>
		{msg && <p>{msg}</p>}
		<div className='mt-4'>
			<ResponsiveGrid eleWidth={eleWidth}>
				<ListCompactCtx.Provider value={compact}>
					{children.map((child, i) => (<div key={i} style={{ width: eleWidth }}>{child}</div>))}
				</ListCompactCtx.Provider>
			</ResponsiveGrid>
		</div>
	</>)
}

export default FormField
