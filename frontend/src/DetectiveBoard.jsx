import { useState, useEffect, useRef } from 'react'

let drag_button_grab = false;

const DragButton = ({rootRef, onDrag, onChange, children, ...otherProps}) => {
	const [drag, setDrag] = useState(false);

	const mouseMove = e => {
		let x = e.pageX, y = e.pageY;
		x -= rootRef.current.getBoundingClientRect().x + window.scrollX;
		y -= rootRef.current.getBoundingClientRect().y + window.scrollY;
		onDrag(x, y);
	}
	const mouseUpDown = (e, val) => {
		if (e.button === 0) {
			if (onChange)
				onChange(val);
			drag_button_grab = val;
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
	}, [drag, mouseMove, mouseUp]);

	return (<button {...otherProps} onMouseDown={mouseDown}>{children}</button>)
}

function Ent({ rootRef, children, pos, fns }) {
	const pinRef = useRef(null);
	const handleRef = useRef(null);
	const frameRef = useRef(null);

	useEffect(() => {
		fns.refs({ pin: pinRef, handle: handleRef, frame: frameRef });
	}, [fns]);

	return (
		<div
			className="item"
			ref={frameRef}
			style={{ position: 'absolute', left: pos.x, top: pos.y, margin: 0 }}
			onMouseEnter={() => { if (!drag_button_grab) fns.hover() }}
		>
			<div style={{ display: 'flex', flexDirection: 'row' }}>
				<div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
					<div className="subitem">
						{children}
					</div>
				</div>
				<div style={{ display: 'flex', flexDirection: 'column' }}>
					<DragButton rootRef={rootRef} ref={handleRef} className="icon-button" onDrag={fns.drag}>🖐️</DragButton>
					<DragButton rootRef={rootRef} ref={pinRef} className="icon-button" onChange={fns.thread} onDrag={fns.dragThread}>🟢️</DragButton>
				</div>
			</div>
		</div>
	)
}


function DetectiveBoard() {
	const make_ent = (id, str, x, y) => { return { id, str, pos: {x, y} }; };
	let [ls, setLs] = useState([
		make_ent(1, 'Is this the real life?', 0, 0),
		make_ent(2, 'Is this just fantasy?', 0, 200),
		make_ent(3, 'Caught in a landslide, no escape from reality', 300, 0),
	]);
	const refs = useRef([]);
	const [cons, setCons] = useState([]);
	const canvasRef = useRef(null);
	const divRef = useRef(null);

	useEffect(() => {
		if (!refs)
			return;
		const pos = [];
		const n = ls.length;
		for (let i = 0; i < n; i++) {
			const pin = refs.current[i].pin.current.getBoundingClientRect();
			const div = divRef.current.getBoundingClientRect();
			pos[ls[i].id] = {
				x: (pin.left + pin.right)/2 - div.x,
				y: (pin.top + pin.bottom)/2 - div.y,
			}
		}

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
				seg(pos[ls[i].id], ls[i].thread);
		}
		ctx.stroke();
	}, [ls, cons]);

	const ch_raw = (i, name, value) => {
		const res = {...ls[i]};
		res[name] = value;
		ls = [].concat(ls.slice(0, i), res, ls.slice(i + 1));
		setLs(ls);
	};
	const ch = (i, name, value) => {
		if (ls[i][name] !== value)
			ch_raw(i, name, value);
	}
	const ch_vec = (i, name, vec) => {
		if ((typeof vec !== typeof ls[i][name]) || (vec && (vec.x != ls[i][name].x || vec.y != ls[i][name].y)))
			ch_raw(i, name, vec);
	};
	const add_vec = (i, name, dx, dy) => ch_vec(i, name, { x: ls[i][name].x + dx, y: ls[i][name].y + dy });
	const bound = (x, sz, mx) => x < 0? 0: x + sz > mx? mx - sz: x;

	const to_top = i => {
		if (i + 1 != ls.length) {
			refs.current = [].concat(refs.current.slice(0, i), refs.current.slice(i+1), [refs.current[i]]);
			ls = [].concat(ls.slice(0, i), ls.slice(i+1), [ls[i]]);
			setLs(ls);
		}
	};

	const try_connect = (id, pos) => {
		let i;
		for (i = ls.length - 1; i >= 0; i--) {
			const p = refs.current[i].pin.current.getBoundingClientRect();
			const d = divRef.current.getBoundingClientRect();
			const x = pos.x + d.x, y = pos.y + d.y;
			if (p.left <= x && x < p.right && p.top <= y && y < p.bottom)
				break;
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

	return (<div className="item"  style={{ position: 'relative', width: '1200px', height: '800px', padding: 0 }}>
		<div ref={divRef} style={{ position: 'absolute', width: '100%', height: '100%', top: 0, left: 0 }}>
			<h1>Board</h1>
			{ls.map((e, i) => (
				<Ent
					key={i}
					pos={e.pos}
					rootRef={divRef}
					fns={{
						hover: () => to_top(i),
						drag: (x, y) => {
							const div = divRef.current;
							const f = refs.current[i].frame.current.getBoundingClientRect();
							const h = refs.current[i].handle.current.getBoundingClientRect();
							x -= (h.left + h.right)/2 - f.left;
							y -= (h.top + h.bottom)/2 - f.top;
							x = bound(x, f.width, div.clientWidth);
							y = bound(y, f.height, div.clientHeight);
							ch_vec(i, 'pos', { x, y });
						},
						dragThread: (x, y) => ch_vec(i, 'thread', { x, y }),
						refs: ref => refs.current[i] = ref,
						thread: v => {
							if (!v) {
								try_connect(e.id, e.thread);
								ch(i, 'thread', undefined);
							}
						},
					}}
				>
					{e.str}
				</Ent>
			))}
			<canvas ref={canvasRef} style={{ position: 'absolute', left: 0, top: 0, pointerEvents: 'none' }}/>
		</div>
	</div>)
}

export default DetectiveBoard
