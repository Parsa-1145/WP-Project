export const SimpleField = (name, body, { id, key }) => (
	<div key={key === undefined? id: key} style={{ position: 'relative' }}>
		<label htmlFor={id} style={{ position: 'absolute', left: 0 }}>{name}: </label>
		<div style={{ marginLeft: '180px', textAlign: 'left' }}>
			{body}
		</div>
	</div>
);

const is_list = (type) => typeof type === 'string' && type.slice(0, 5) == 'list ';

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

	else if (is_list(type)) {
		const eles = type.split(' ').slice(1);
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

export const FormField = (type, name, value, { id, key, compact }) => {
	if (key === undefined) key = id;

	if (!compact) {
		const imgStyle = { margin: '0 auto', maxWidth: '500px' };

		if (type === 'file') // image
			return (<img key={key} src={value} style={imgStyle}/>);

		else if (type === 'files') // images
			return (<div key={key}>{value.map((src, i) => (<img key={i} src={src} style={imgStyle}/>))}</div>);

		else if (type === 'list Key Value')
			return (<div key={key}>{Object.entries(value).map((kv, i) => SimpleField(kv[0], (<p>{kv[1]||'<empty>'}</p>), { key: i }))}</div>);

		else if (is_list(type)) {
			const enames = type.split(' ').slice(1);
			return (
				<div key={key}>
					<p>{name}</p>
					<div key={i} style={{ display: 'flex', flexDirection: 'row' }}>
						{enames.map((ename, j) => (<h6 key={j} style={{ flex: 1, textAlign: 'left' }}>{ename}</h6>))}
					</div>
					{value.map((ent, i) => (
						<div key={i} style={{ display: 'flex', flexDirection: 'row' }}>
							{ent.map((ele, j) => (<p key={j} style={{ flex: 1, textAlign: 'left' }}>{ele || '<empty>'}</p>))}
						</div>
					))}
				</div>
			);
		}

		else
			return SimpleField(name, (<p>{value||'<empty>'}</p>), { id, key });
	}

	else {
		const imgStyle = { margin: 0, maxWidth: '400px', maxHeight: '300px' };

		if (type === 'file') // image
			return (<img key={key} src={value} style={imgStyle}/>);

		else if (type === 'files') // images
			return (<div key={key}>{value.map((src, i) => (<img key={i} src={src} style={imgStyle}/>))}</div>);

		else if (type === 'list Key Value')
			return (<div key={key}>{Object.entries(value).map((kv, i) => SimpleField(kv[0], (<div>{kv[1]||'<empty>'}</div>), { key: i }))}</div>);

		// else if (is_list(type))
		// 	TODO

		else
			return SimpleField(name, (<div>{value||'<empty>'}</div>), { id, key });
	}
}

export default FormField
