import { useContext } from 'react'
import { GenericList, FormField, ListCompactCtx } from '../Forms'

const flatten_list = (data) => {
	if (!Array.isArray(data))
		return [];
	// backend example: [[{...}, {...}]]
	if (data.length === 1 && Array.isArray(data[0]))
		return data[0];
	return data.flat();
};

const fmt_num = (n) => {
	if (typeof n !== 'number')
		return n ?? '<empty>';
	return n.toLocaleString();
};

function WantedFrame({ person, rank }) {
	const compact = useContext(ListCompactCtx);
	const fullName = [person?.first_name, person?.last_name].filter(Boolean).join(' ') || '<empty>';
	return (
		<div className='item'>
			<h3 className='text-left'>{rank}. {fullName}</h3>
			{FormField('text', 'Username', person?.username, { id: `u-${person?.id}`, key: 'username', compact })}
			{FormField('number', 'Reward Amount', fmt_num(person?.reward_amount), { key: 'reward', compact })}
			{FormField('number', 'Wanted Score', fmt_num(person?.wanted_score), { key: 'score', compact })}
		</div>
	);
}

export default function MostWantedList({ list, title = 'Most Wanted', onReload, onReturn }) {
	const flat = flatten_list(list);
	return (
		<div className='relative w-full h-full'>
			<GenericList title={title} onReload={onReload} onReturn={onReturn}>
				{flat.map((p, i) => (<WantedFrame key={p?.id ?? i} person={p} rank={i + 1} />))}
			</GenericList>
		</div>
	);
}
