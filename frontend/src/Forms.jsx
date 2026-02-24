import { useState, useEffect, createContext, useContext } from 'react'

export const SimpleField = (name, body, { id, key, compact, style }) => {
	if (key === undefined) key = id;
	return (
		<div key={key} style={{ position: 'relative' }}>
			<label htmlFor={id} style={{ ...style, position: 'absolute', left: 0 }}>{name}: </label>
			<div style={{ ...style, marginLeft: compact >= 2? '110px': '180px', textAlign: 'left' }}>
				{body}
			</div>
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

	const Simple = body => SimpleField(name, body, { id, key });

	if (type === 'textarea')
		return Simple((<textarea id={id} value={value} onChange={onChange}/>));

	else if (type === 'file')
		return Simple((<input id={id} type={'file'} onChange={onChange}/>));

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
		// TODO: determine timezone
		// 2026-02-18T17:51:45.491058+03:30
		// 2026-02-19T02:12
		const value_small = value.split(':').slice(0, 2).join(':');
		return Simple((<div><input id={id} type={'datetime-local'} value={value_small} onChange={onChange}/>UTC+03:30</div>));
	}

	else if (is_list(type)) {
		const eles = parse_list(type, true);
		return (
			<div key={id} style={{ position: 'relative' }}>
				<label htmlFor={id} style={{ position: 'absolute', left: 0 }}>{name}: </label>

				<div id={id} style={{ flex: 1, display: 'flex', flexDirection: 'column', textAlign: 'left', marginLeft: '180px' }}>
					{value && value.map((ent, i) => (
						<div
							key={i}
							style={{ display: 'flex', flexDirection: 'row' }}
						>
							{eles.map((ele, j) => (
								<input key={j} value={ent[j]} placeholder={ele} type='text' onChange={e => {
									const ent2 = [...ent];
									ent2[j] = e.target.value;
									onChange([i, ent2])
								}} />
							))}
							<button onClick={() => onChange(i)}>Remove</button>
						</div>
					))}

					<button onClick={() => onChange([value.length, eles.map(() => '')])}>New</button>
				</div>
			</div>
		);
	}

	else
		return Simple((<input id={id} type={type} value={value} onChange={onChange}/>));
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
		// TODO: determine timezone
		// 2026-02-18T17:51:45.491058+03:30
		// 2026-02-19T02:12
		data2[name] = e.target.value + ":00+03:30";
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

		else
			return SimpleField(name, (<p>{value||'<empty>'}</p>), { id, key });
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
				value = value.replace(/\:\d{2}(\.\d+)?(?=[+-]|$)/, '').replace(/T/g, ' ');
			return SimpleField(name, (<div>{value||'<empty>'}</div>), { id, key, style: divStyle, compact });
		}
	}
}

export const ResponsiveGrid = ({ eleWidth, children, ...props }) => {
	const [width, setWidth] = useState(window.innerWidth);
	useEffect(() => {
		const handle = () => setWidth(window.innerWidth);
		window.addEventListener('resize', handle);
		return () => window.removeEventListener('resize', handle);
	}, []);
	const rowSize = Math.max(1, Math.floor(width * 0.9 / eleWidth));
	const divWidth = eleWidth * rowSize;
	return (
		<div style={{
			display: 'grid',
			gridTemplateColumns: 'repeat(' + rowSize + ', 1fr)',
			gridTemplateRows: 'auto',
			width: divWidth,
		}}>
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


export function GenericList({ children, title, onReload, onReturn, msg }) {
	const [compact, setCompact] = useState(true);
	const eleWidth = compact? 450: 550;
	return (<>
		<div className='flex flex-col'>
			<div className='flex flex-row shrink w-full gap-2'>
				<h2 className='text-left grow'>{title}</h2>
				<label>
					<input type='checkbox' checked={compact} onChange={() => setCompact(!compact)} />
					Compact View
				</label>
				{ onReload && (<button onClick={onReload}>Reload</button>) }
				{ onReturn && (<button onClick={onReturn}>Return</button>) }
			</div>
		</div>
		{msg && <p>{msg}</p>}
		<ResponsiveGrid eleWidth={eleWidth}>
			<ListCompactCtx.Provider value={compact}>
				{children.map((child, i) => (<div key={i} style={{ width: eleWidth }}>{child}</div>))}
			</ListCompactCtx.Provider>
		</ResponsiveGrid>
	</>)
}

export default FormField
