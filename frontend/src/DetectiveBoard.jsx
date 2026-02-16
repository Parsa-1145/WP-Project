import { useState, useEffect, useRef } from 'react'

const DragButton = ({onDrag, onChange, children, ...otherProps}) => {
	const [drag, setDrag] = useState(false);

	const mouseMove = e => onDrag(e.movementX, e.movementY);
	const mouseUpDown = (e, val) => {
		if (e.button === 0) {
			if (onChange)
				onChange(val);
			setDrag(val);
		}
	};
	const mouseDown = e => mouseUpDown(e, true);
	const mouseUp = e => mouseUpDown(e, false);

	useEffect(() => {
		if (drag) {
			window.addEventListener('mousemove', mouseMove);
			window.addEventListener('mouseup', mouseUp);
			return () => {
				window.removeEventListener('mousemove', mouseMove);
				window.removeEventListener('mouseup', mouseUp);
			}
		}
	}, [drag, onDrag]);

	return (<button {...otherProps} onMouseDown={mouseDown}>{children}</button>)
}

function Ent({ children, pos, fns }) {
	const pinRef = useRef(null);
	useEffect(() => {
		const e = pinRef.current;
		fns.pinPos(e.offsetLeft + e.offsetWidth/2, e.offsetTop + e.offsetHeight/2)
	}, [pos]);
	return (
		<div
			className="item"
			style={{ position: 'absolute', left: pos.x, top: pos.y, margin: 0 }}
			onMouseEnter={fns.hover}
		>
			<div style={{ display: 'flex', flexDirection: 'row' }}>
				<div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
					<div className="subitem">
						{children}
					</div>
				</div>
				<div style={{ display: 'flex', flexDirection: 'column' }}>
					<DragButton className="icon-button" onDrag={fns.drag}>🖐️</DragButton>
					<DragButton ref={pinRef} className="icon-button" onChange={fns.thread} onDrag={fns.dragThread}>🟢️</DragButton>
				</div>
			</div>
		</div>
	)
}


function DetectiveBoard() {
	const make_ent = (id, str, x, y) => { return { id, str, pos: {x, y}, pin: {x: 0, y: 0}, thread: undefined}; };
	const [ls, setLs] = useState([
		make_ent(1, 'Is this the real life?', 0, 0),
		make_ent(2, 'Is this just fantasy?', 0, 200),
		make_ent(3, 'Caught in a landslide, no escape from reality', 300, 0),
	]);
	const [cons, setCons] = useState([]);
	const canvasRef = useRef(null);
	const divRef = useRef(null);

	useEffect(() => {
		const pos = [];
		const n = ls.length;
		for (let i = 0; i < n; i++)
			pos[ls[i].id] = ls[i].pin;

		const canvas = canvasRef.current;
		const div = divRef.current;

		const ctx = canvas.getContext('2d');

		canvas.width = div.clientWidth;
		canvas.height = div.clientHeight;

		const seg = (p, q) => {
			ctx.moveTo(p.x, p.y);
			ctx.lineTo(q.x, q.y);
		};

		ctx.clearRect(0, 0, canvas.width, canvas.height);

		ctx.beginPath();
		ctx.lineWidth = 5;
		ctx.strokeStyle = 'rgb(191, 31, 31)';
		for (const con of cons)
			seg(pos[con[0]], pos[con[1]]);
		ctx.stroke();

		ctx.beginPath();
		ctx.lineWidth = 5;
		ctx.strokeStyle = 'rgb(31, 31, 191)';
		for (let i = 0; i < n; i++) {
			if (ls[i].thread)
				seg(ls[i].pin, ls[i].thread);
		}
		ctx.stroke();
	}, [divRef, ls, cons]);

	const ch_vec = (i, name, vec) => {
		if ((typeof vec !== typeof ls[i][name]) || (vec && (vec.x != ls[i][name].x || vec.y != ls[i][name].y))) {
			const res = {...ls[i]};
			res[name] = vec? {x: vec.x, y: vec.y}: vec;
			setLs([].concat(ls.slice(0, i), res, ls.slice(i + 1)));
		}
	};
	const add_vec = (i, name, dx, dy) => ch_vec(i, name, { x: ls[i][name].x + dx, y: ls[i][name].y + dy });

	const to_top = i => {
		 if (i + 1 != ls.length)
			 setLs([].concat(ls.slice(0, i), ls.slice(i+1), ls[i]));
	};

	const try_connect = (id, pos) => {
		let i;
		for (i = ls.length - 1; i >= 0; i--) {
			if (   ls[i].pin.x - 16 <= pos.x && pos.x < ls[i].pin.x + 16
			    && ls[i].pin.y - 16 <= pos.y && pos.y < ls[i].pin.y + 16)
						break
		}
		if (i < 0 || ls[i].id === id)
			return;
		let con;
		for (con = 0; con < cons.length; con++) {
			if (cons[con][0] === id && cons[con][1] === ls[i].id) break;
			if (cons[con][1] === id && cons[con][0] === ls[i].id) break;
		}
		if (con == cons.length)
			setCons(cons.concat([[id, ls[i].id]]))
		else
			setCons([].concat(cons.slice(0, con), cons.slice(con + 1)));
	}

	return (<div className="item" ref={divRef} style={{ position: 'relative', width: '1200px', height: '600px' }}>
		<h1>Hello</h1>
		{ls.map((e, i) => (
			<Ent
				key={i}
				pos={{ x: e.pos.x, y: e.pos.y }}
				fns={{
					hover: () => to_top(i),
					drag: (dx, dy) => add_vec(i, 'pos', dx, dy),
					dragThread: (dx, dy) => add_vec(i, 'thread', dx, dy),
					pinPos: (x, y) => ch_vec(i, 'pin', {x: x + e.pos.x, y: y + e.pos.y}),
					thread: v => {
						if (!v) try_connect(e.id, e.thread);
						ch_vec(i, 'thread', v? e.pin: undefined);
					},
				}}
			>
				{e.str}
			</Ent>
		))}
		<canvas ref={canvasRef} style={{ position: 'absolute', left: 0, top: 0, pointerEvents: 'none' }}/>
	</div>)
}

export default DetectiveBoard
