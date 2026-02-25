import { useState, useEffect, useRef } from 'react'
import { EvidenceFrame, EvidenceList } from './Evidence'
import { ListCompactCtx } from './Forms'
import { session, error_msg_list } from './session'
import html2canvas from 'html2canvas'

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

function Item({ rootRef, children, pos, fns }) {
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
					{children}
				</div>
				<div style={{ display: 'flex', flexDirection: 'column' }}>
					<DragButton rootRef={rootRef} ref={handleRef} className="icon-button" onDrag={fns.drag}>🖐️</DragButton>
					<DragButton rootRef={rootRef} ref={pinRef} className="icon-button" onChange={fns.thread} onDrag={fns.dragThread}>🟢️</DragButton>
					<button className="icon-button" onClick={fns.remove}>❌️</button>
				</div>
			</div>
		</div>
	)
}


function DetectiveBoardBoard({ captureRef, evi_list, ls, setLs, cons, setCons, title }) {
	const refs = useRef([]);
	const divRef = useRef(null);
	const canvasRef = useRef(null);

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

	const remove = i => {
		const id = ls[i].id;
		ls = [].concat(ls.slice(0, i), ls.slice(i + 1));
		cons = cons.filter(([x, y]) => x !== id && y !== id);
		setLs(ls);
		setCons(cons);
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

	return (<div ref={captureRef} className="item" style={{ margin: 'auto', position: 'relative', width: '1200px', height: '800px', padding: 0 }}>
		<div ref={divRef} style={{ position: 'absolute', width: '100%', height: '100%', top: 0, left: 0 }}>
			<h1>{title}</h1>
			{ls.map((e, i) => (
				<Item
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
						remove: () => remove(i),
					}}
				>
					<div style={{ maxWidth: '300px' }}>
						<ListCompactCtx.Provider value={2}>
							<EvidenceFrame evi={evi_list.find(evi => evi.id === e.evi_id)} className='subitem'/>
						</ListCompactCtx.Provider>
					</div>
				</Item>
			))}
			<canvas ref={canvasRef} style={{ position: 'absolute', left: 0, top: 0, pointerEvents: 'none' }}/>
		</div>
	</div>)
}

const DetectiveBoardPicker = ({ evi_list, onSelect }) => EvidenceList({
	list: evi_list, title: 'Select Evidence', onReturn: () => onSelect(null), onSelect
});

function DetectiveBoard({ evi_list, item_list, con_list, case_id, onReload }) {
	const [selecting, setSelecting] = useState(false);
	const [ls, setLs] = useState(item_list || []);
	const [cons, setCons] = useState(con_list || []);
	const [post, setPost] = useState(false);
	const [msgs, setMsgs] = useState([]);
	const setMsg = msg => setMsgs([msg]);
	const captureRef = useRef(null);

	const genId = () => {
		for (let i = 0;; i++) {
			if (!ls.some(item => item.id === i))
				return i;
		}
	}

	if (selecting) return DetectiveBoardPicker({ evi_list: evi_list, onSelect: evi => {
		setSelecting(false);
		if (evi !== null)
			setLs([...ls, { id: genId(), evi_id: evi.id, pos: { x: 0, y: 0 } }]);
	}});

	const submit = () => {
		const req_fields = [ 'id', 'evi_id', 'pos' ];
		const req_ls = ls.map(ent => {
			const res = {};
			for (const field of req_fields)
				res[field] = ent[field];
			return res;
		});
		const req = { board_json: { items: req_ls, cons } };

		setPost(true);
		setMsg('Awaiting response...');

		session.put(`/api/cases/${case_id}/detective-board/`, req)
			.then(() => {
				setMsg('Saved successfully');
			})
			.catch(err => setMsgs(error_msg_list(err)))
			.finally(() => setPost(false));
	};

	const capture = () => html2canvas(captureRef.current, { useCORS: true }).then(canvas => canvas.toBlob(blob => {
		const link = document.createElement('a');
		link.href = URL.createObjectURL(blob);
		link.download = `case-${case_id}-board.png`;
		link.click();
	}));

	return (<>
		{msgs.map((x, i) => <p key={i} style={{ textAlign: 'center' }}>{x}</p>)}
		<div className="flex flex-row h-full">
			<div className="flex flex-col">
				{ onReload && <button onClick={onReload} disabled={post}>Reload</button> }
				<button onClick={() => setSelecting(true)}>Add Evi.</button>
				<button onClick={capture}>Capture</button>
				<button onClick={submit} disabled={post}>Save</button>
			</div>
			<DetectiveBoardBoard {...{ evi_list, ls, setLs, cons, setCons, captureRef, title: `Case ${case_id} Board` }}/>
		</div>
	</>);
}

export default DetectiveBoard;
